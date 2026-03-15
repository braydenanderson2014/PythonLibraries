from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
                             QComboBox, QDateEdit, QDoubleSpinBox, QDialog, QFormLayout,
                             QDialogButtonBox, QTextEdit, QTabWidget, QGroupBox, QCheckBox,
                             QMessageBox, QSplitter, QStyledItemDelegate, QAbstractItemView,
                             QGridLayout)
from PyQt6.QtCore import Qt, QDate, QModelIndex
from PyQt6.QtGui import QFont, QColor, QBrush
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas  # type: ignore
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import sys, os, csv
from datetime import date, datetime, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.bank import Bank
from src.account_unified import AccountManager
from src.budget import BudgetManager, Budget
from src.transaction_rules import RuleManager
from src.goals import GoalManager, Goal
from src.net_worth import NetWorthTracker, NetWorthSnapshot
from src.tags import TagManager, Tag
from ui.banking_api_widget import BankingAPIWidget
from ui.stock_manager_widget import StockManagerWidget
from assets.Logger import Logger

logger = Logger()

class SimpleComboDelegate(QStyledItemDelegate):
    """Simple, robust delegate for dropdown selection"""
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items if items else []

    def createEditor(self, parent, option, index):
        """Create a simple combo box"""
        try:
            # Guard against invalid parent/editor creation
            if parent is None:
                raise RuntimeError("Delegate createEditor received None parent")
            combo = QComboBox(parent)
            combo.addItems(self.items)
            combo.setEditable(False)  # Disable editing to prevent issues
            # Borderless style to avoid visual overlap with cell borders
            combo.setStyleSheet(
                "QComboBox { border: 0px; padding-left: 2px; padding-right: 14px; }"
            )
            return combo
        except Exception as e:
            print(f"[ERROR] SimpleComboDelegate.createEditor: Error creating editor: {e}")
            import traceback
            traceback.print_exc()
            return None

    def updateEditorGeometry(self, editor, option, index):
        """Ensure the editor fits snugly within the cell to prevent overlay glitches"""
        try:
            if editor is not None:
                editor.setGeometry(option.rect.adjusted(1, 1, -1, -1))
        except Exception as e:
            logger.error("SimpleComboDelegate", f"updateEditorGeometry error: {e}")

    def setEditorData(self, editor, index):
        """Set current value"""
        try:
            if editor and self.items:
                combo = editor  # Type: QComboBox
                current_text = index.data(Qt.ItemDataRole.DisplayRole)
                if current_text and str(current_text) in self.items:
                    combo.setCurrentText(str(current_text))  # type: ignore
                else:
                    combo.setCurrentIndex(0)  # type: ignore
        except Exception as e:
            logger.error("SimpleComboDelegate", f"Error setting editor data: {e}")
            import traceback
            traceback.print_exc()

    def setModelData(self, editor, model, index):
        """Save selected value"""
        try:
            if editor and model is not None:
                combo = editor  # Type: QComboBox
                selected_text = combo.currentText()  # type: ignore
                model.setData(index, selected_text)
        except Exception as e:
            logger.error("SimpleComboDelegate", f"Error setting model data: {e}")
            import traceback
            traceback.print_exc()

class SimpleDateDelegate(QStyledItemDelegate):
    """Simple date picker delegate"""
    def createEditor(self, parent, option, index):
        """Create date picker"""
        try:
            if parent is None:
                raise RuntimeError("DateDelegate createEditor received None parent")
            date_edit = QDateEdit(parent)
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat('yyyy-MM-dd')
            date_edit.setStyleSheet(
                "QDateEdit { border: 0px; padding-left: 2px; padding-right: 2px; }"
            )
            return date_edit
        except Exception as e:
            print(f"[ERROR] SimpleDateDelegate.createEditor: Error creating date editor: {e}")
            import traceback
            traceback.print_exc()
            return None

    def updateEditorGeometry(self, editor, option, index):
        """Ensure the editor fits snugly within the cell to prevent overlay glitches"""
        try:
            if editor is not None:
                editor.setGeometry(option.rect.adjusted(1, 1, -1, -1))
        except Exception as e:
            logger.error("SimpleDateDelegate", f"updateEditorGeometry error: {e}")

    def setEditorData(self, editor, index):
        """Set current date"""
        try:
            if editor:
                date_edit = editor  # Type: QDateEdit
                current_text = index.data(Qt.ItemDataRole.DisplayRole)
                if current_text:
                    try:
                        date_obj = QDate.fromString(current_text, 'yyyy-MM-dd')
                        date_edit.setDate(date_obj)  # type: ignore
                    except:
                        date_edit.setDate(QDate.currentDate())  # type: ignore
        except Exception as e:
            logger.error("SimpleDateDelegate", f"Error setting editor data: {e}")
            import traceback
            traceback.print_exc()

    def setModelData(self, editor, model, index):
        """Save selected date"""
        try:
            if editor and model is not None:
                date_edit = editor  # Type: QDateEdit
                date_str = date_edit.date().toString('yyyy-MM-dd')  # type: ignore
                model.setData(index, date_str)
        except Exception as e:
            logger.error("SimpleDateDelegate", f"Error setting model data: {e}")
            import traceback
            traceback.print_exc()

class SimpleAmountDelegate(QStyledItemDelegate):
    """Simple amount editor delegate"""
    def createEditor(self, parent, option, index):
        """Create numeric input"""
        try:
            spin = QDoubleSpinBox(parent)
            spin.setMinimum(0.01)
            spin.setMaximum(999999.99)
            spin.setDecimals(2)
            spin.setPrefix("$")
            spin.setStyleSheet(
                "QDoubleSpinBox { border: 0px; padding-left: 2px; padding-right: 2px; }"
            )
            return spin
        except Exception as e:
            print(f"[ERROR] SimpleAmountDelegate.createEditor: Error creating amount editor: {e}")
            import traceback
            traceback.print_exc()
            return None

    def setEditorData(self, editor, index):
        """Set current amount"""
        try:
            if editor:
                spin_box = editor  # Type: QDoubleSpinBox
                current_text = index.data(Qt.ItemDataRole.DisplayRole)
                if current_text:
                    try:
                        # Clean and convert
                        clean_value = str(current_text).replace('$', '').replace(',', '')
                        spin_box.setValue(float(clean_value))  # type: ignore
                    except:
                        spin_box.setValue(0.00)  # type: ignore
        except Exception as e:
            logger.error("SimpleAmountDelegate", f"Error setting editor data: {e}")
            import traceback
            traceback.print_exc()

    def setModelData(self, editor, model, index):
        """Save amount"""
        try:
            if editor and model is not None:
                spin_box = editor  # Type: QDoubleSpinBox
                model.setData(index, f"{spin_box.value():.2f}")  # type: ignore
        except Exception as e:
            logger.error("SimpleAmountDelegate", f"Error setting model data: {e}")
            import traceback
            traceback.print_exc()

    def updateEditorGeometry(self, editor, option, index):
        """Ensure the editor fits snugly within the cell to prevent overlay glitches"""
        try:
            if editor is not None:
                editor.setGeometry(option.rect.adjusted(1, 1, -1, -1))
        except Exception as e:
            logger.error("SimpleAmountDelegate", f"updateEditorGeometry error: {e}")

class AddTransactionDialog(QDialog):
    def __init__(self, parent=None, bank=None, is_recurring=False):
        super().__init__(parent)
        self.bank = bank
        self.is_recurring = is_recurring
        self.setWindowTitle('Add Recurring Transaction' if is_recurring else 'Add Transaction')
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # Amount
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMaximum(999999.99)
        self.amount_spin.setPrefix('$')
        layout.addRow('Amount:', self.amount_spin)
        
        # Type (Income/Expense/Loan Payment)
        self.type_combo = QComboBox()
        if is_recurring:
            self.type_combo.addItems(['Income', 'Expense', 'Loan Payment'])
        else:
            self.type_combo.addItems(['Income', 'Expense'])
        layout.addRow('Type:', self.type_combo)
        
        # Description
        self.desc_edit = QLineEdit()
        layout.addRow('Description:', self.desc_edit)
        
        # Account (now shows specific bank accounts) - renamed to Pay From for recurring
        if is_recurring:
            # For recurring transactions, use Pay From and Pay To
            self.pay_from_combo = QComboBox()
            if bank:
                # Get user's bank accounts (exclude loan accounts for pay from)
                accounts = bank.get_accounts_summary(bank.current_user_id)
                if accounts:
                    for account_info in accounts:
                        display_name = account_info['display_name']
                        balance = account_info['balance']
                        # Exclude loan accounts from pay from options
                        if 'loan' not in display_name.lower():
                            self.pay_from_combo.addItem(f"{display_name} (${balance:,.2f})", account_info['account_id'])
                else:
                    self.pay_from_combo.addItem("No accounts - Please add accounts first", None)
            layout.addRow('Pay From:', self.pay_from_combo)
            
            # Pay To field (will be populated based on transaction type)
            self.pay_to_combo = QComboBox()
            self.pay_to_combo.setEditable(True)  # Allow custom entries
            layout.addRow('Pay To:', self.pay_to_combo)
        else:
            # For regular transactions, keep the original account field
            self.account_combo = QComboBox()
            if bank:
                # Get user's bank accounts
                accounts = bank.get_accounts_summary(bank.current_user_id)
                if accounts:
                    for account_info in accounts:
                        display_name = account_info['display_name']
                        balance = account_info['balance']
                        self.account_combo.addItem(f"{display_name} (${balance:,.2f})", account_info['account_id'])
                else:
                    # No accounts setup yet, show message
                    self.account_combo.addItem("No accounts - Please add accounts first", None)
            else:
                # Fallback to generic account field
                self.account_edit = QLineEdit()
                self.account_edit.setPlaceholderText('e.g., Checking, Savings, Cash')
                layout.addRow('Account:', self.account_edit)
                
            if hasattr(self, 'account_combo'):
                layout.addRow('Account:', self.account_combo)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        if is_recurring:
            categories = [
                'Salary', 'Bonus', 'Investment Income', 'Rental Income', 'Side Hustle',  # Income categories
                'Rent/Mortgage', 'Utilities', 'Insurance', 'Loan Payment', 'Subscription',  # Bills
                'Groceries', 'Restaurant', 'Transportation', 'Gas', 'Car Maintenance',  # Living expenses
                'Healthcare', 'Medication', 'Gym/Fitness', 'Phone', 'Internet',  # Services
                'Investment', 'Savings', 'Emergency Fund', 'Retirement',  # Financial
                'Entertainment', 'Shopping', 'Travel', 'Education', 'Charity',  # Discretionary
                'Home Maintenance', 'Property Tax', 'HOA Fees', 'Childcare',  # Property/Family
                'Business Expense', 'Office Supplies', 'Professional Services',  # Business
                'Other'
            ]
        else:
            categories = [
                # Income categories
                'Salary', 'Bonus', 'Investment Income', 'Rental Income', 'Freelance', 'Gift Received', 'Refund',
                # Essential expenses
                'Groceries', 'Restaurant', 'Fast Food', 'Rent/Mortgage', 'Utilities', 'Phone', 'Internet',
                'Transportation', 'Gas', 'Car Maintenance', 'Insurance', 'Healthcare', 'Medication',
                # Discretionary spending
                'Entertainment', 'Shopping', 'Clothing', 'Travel', 'Hobbies', 'Sports', 'Books',
                'Subscription', 'Gaming', 'Movies', 'Streaming Services',
                # Financial
                'Investment', 'Savings', 'Emergency Fund', 'Retirement', 'Loan Payment', 'Credit Card Payment',
                'Bank Fees', 'ATM Fees', 'Interest Paid',
                # Home & Property
                'Home Maintenance', 'Home Improvement', 'Property Tax', 'HOA Fees', 'Rent Utilities',
                'Cleaning Supplies', 'Garden/Yard',
                # Family & Personal
                'Childcare', 'Education', 'School Supplies', 'Pet Care', 'Personal Care', 'Haircut',
                'Beauty Products', 'Gifts Given', 'Charity', 'Donations',
                # Business
                'Business Expense', 'Office Supplies', 'Professional Services', 'Business Travel',
                'Business Meals', 'Equipment', 'Software', 'Training',
                # Other
                'Miscellaneous', 'Cash Withdrawal', 'Transfer', 'Other'
            ]
        self.category_combo.addItems(categories)
        layout.addRow('Category:', self.category_combo)
        
        # Split transaction section (only for regular transactions, not recurring)
        if not is_recurring:
            self.splits_data = []  # Store split data
            
            split_layout = QHBoxLayout()
            self.split_checkbox = QCheckBox('Split this transaction across multiple categories')
            self.split_checkbox.stateChanged.connect(self.on_split_checkbox_changed)
            split_layout.addWidget(self.split_checkbox)
            
            self.split_edit_btn = QPushButton('Edit Splits')
            self.split_edit_btn.setEnabled(False)
            self.split_edit_btn.clicked.connect(self.open_split_dialog)
            split_layout.addWidget(self.split_edit_btn)
            
            layout.addRow('', split_layout)
            
            # Split summary label
            self.split_summary_label = QLabel('')
            self.split_summary_label.setWordWrap(True)
            self.split_summary_label.setStyleSheet('color: #666; font-style: italic;')
            layout.addRow('', self.split_summary_label)
            
            # Attachments section (only for regular transactions)
            from src.attachment_manager import AttachmentManager
            self.attachment_manager = AttachmentManager()
            self.attachments_data = []  # Store attachment data
            
            attachments_label = QLabel('Attachments (Receipts, Invoices, etc.):')
            layout.addRow(attachments_label)
            
            # Attachments list
            self.attachments_list = QTableWidget()
            self.attachments_list.setColumnCount(4)
            self.attachments_list.setHorizontalHeaderLabels(['📎', 'Filename', 'Size', 'Actions'])
            self.attachments_list.horizontalHeader().setStretchLastSection(False)
            self.attachments_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            self.attachments_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.attachments_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            self.attachments_list.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            self.attachments_list.setColumnWidth(0, 40)
            self.attachments_list.setColumnWidth(2, 80)
            self.attachments_list.setColumnWidth(3, 120)
            self.attachments_list.setMaximumHeight(150)
            layout.addRow(self.attachments_list)
            
            # Attachment buttons
            attach_btn_layout = QHBoxLayout()
            
            self.add_attachment_btn = QPushButton('📎 Add Attachment')
            self.add_attachment_btn.clicked.connect(self.add_attachment)
            attach_btn_layout.addWidget(self.add_attachment_btn)
            
            attach_btn_layout.addStretch()
            
            layout.addRow('', attach_btn_layout)
        
        # Recurring-specific fields
        if is_recurring:
            self.frequency_combo = QComboBox()
            self.frequency_combo.addItems(['weekly', 'monthly', 'yearly'])
            layout.addRow('Frequency:', self.frequency_combo)
            
            self.start_date = QDateEdit()
            self.start_date.setCalendarPopup(True)
            self.start_date.setDate(QDate.currentDate())
            layout.addRow('Start Date:', self.start_date)
            
            self.end_date = QDateEdit()
            self.end_date.setCalendarPopup(True)
            self.end_date.setDate(QDate.currentDate().addYears(1))
            layout.addRow('End Date (Optional):', self.end_date)
            
            self.indefinite_check = QCheckBox('Indefinite (no end date)')
            layout.addRow('', self.indefinite_check)
            
            # Connect signal for type changes to update Pay To field
            self.type_combo.currentTextChanged.connect(self.on_type_changed)
        else:
            # Connect account selection to auto-detect loan accounts
            if hasattr(self, 'account_combo'):
                self.account_combo.currentTextChanged.connect(self.on_account_changed)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def on_type_changed(self, type_text):
        """Handle changes to transaction type for auto-populating Pay To field"""
        if not hasattr(self, 'pay_to_combo'):
            return
            
        self.pay_to_combo.clear()
        
        if type_text == 'Loan Payment':
            # Auto-populate with loan accounts
            if self.bank:
                try:
                    loans = self.bank.list_loans(self.bank.current_user_id)
                    if loans:
                        for loan in loans:
                            # Handle both dict and Loan object access
                            if hasattr(loan, 'desc'):
                                # Loan object - use correct attribute names
                                loan_name = loan.desc if loan.desc else f"Loan {loan.identifier}"
                                balance = getattr(loan, 'remaining_principal', 0)
                                payment_amount = getattr(loan, 'minimum_payment', getattr(loan, 'payment_amount', 0))
                                loan_id = loan.identifier
                            else:
                                # Dictionary
                                loan_name = loan.get('desc', f"Loan {loan.get('identifier', 'Unknown')}")
                                balance = loan.get('remaining_principal', 0)
                                payment_amount = loan.get('minimum_payment', loan.get('payment_amount', 0))
                                loan_id = loan.get('identifier')
                            
                            # Store payment amount in item data for auto-population
                            item_data = {'id': loan_id, 'payment_amount': payment_amount}
                            self.pay_to_combo.addItem(f"{loan_name} (${balance:,.2f})", item_data)
                            
                        # Connect signal to auto-populate amount when loan is selected
                        self.pay_to_combo.currentIndexChanged.connect(self.on_loan_selected)
                    else:
                        self.pay_to_combo.addItem("No loans found", None)
                except Exception as e:
                    logger.warning("AddTransactionDialog", f"Could not load loans for auto-population: {e}")
                    self.pay_to_combo.addItem("Error loading loans", None)
        else:
            # For other types, allow free-form entry and clear amount
            self.pay_to_combo.setCurrentText("")
            # Add some common payees as suggestions
            common_payees = ['Utility Company', 'Landlord', 'Insurance Company', 'Store', 'Service Provider']
            self.pay_to_combo.addItems(common_payees)
            # Disconnect loan selection signal if it exists
            try:
                self.pay_to_combo.currentIndexChanged.disconnect(self.on_loan_selected)
            except:
                pass  # Signal wasn't connected
    
    def on_loan_selected(self):
        """Auto-populate amount when a loan is selected"""
        if not hasattr(self, 'pay_to_combo') or not hasattr(self, 'amount_spin'):
            return
            
        current_data = self.pay_to_combo.currentData()
        if current_data and isinstance(current_data, dict):
            payment_amount = current_data.get('payment_amount', 0)
            if payment_amount > 0:
                self.amount_spin.setValue(payment_amount)
                print(f"[DEBUG] Auto-populated amount: ${payment_amount}")
                logger.debug("AddTransactionDialog", f"Auto-populated amount: ${payment_amount}")
            else:
                logger.debug("AddTransactionDialog", "No loan data found for auto-population")
    def on_account_changed(self, account_text):
        """Auto-detect loan accounts and set type to 'Loan Payment'"""
        if not self.bank or not hasattr(self, 'type_combo'):
            return
            
        try:
            # Extract account name from display text (remove balance info)
            account_name = account_text.split(' (')[0] if '(' in account_text else account_text
            
            # Check if this account is associated with a loan
            if self.bank.is_loan_account(account_name, self.bank.current_user_id):
                # Auto-set type to Loan Payment if available
                type_index = self.type_combo.findText('Loan Payment')
                if type_index >= 0:
                    self.type_combo.setCurrentIndex(type_index)
                    print(f"[DEBUG] Auto-detected loan account '{account_name}' - set type to Loan Payment")
                    
                    # Auto-populate amount if we can find the loan
                    loan = self.bank.get_loan_for_account(account_name, self.bank.current_user_id)
                    if loan and hasattr(self, 'amount_spin'):
                        if loan.payment_amount > 0:
                            self.amount_spin.setValue(loan.payment_amount)
                            print(f"[DEBUG] Auto-populated loan payment amount: ${loan.payment_amount}")
            else:
                # Reset to Income/Expense if not a loan account
                current_type = self.type_combo.currentText()
                if current_type == 'Loan Payment':
                    self.type_combo.setCurrentIndex(0)  # Reset to first option (Income)
                    print(f"[DEBUG] Non-loan account '{account_name}' - reset type from Loan Payment")
        except Exception as e:
            print(f"[WARNING] Error in account change detection: {e}")
    
    def get_data(self):
        # Handle account selection for recurring vs regular transactions
        if self.is_recurring:
            # For recurring transactions, use Pay From and Pay To
            if hasattr(self, 'pay_from_combo'):
                pay_from_id = self.pay_from_combo.currentData()
                pay_from_name = self.pay_from_combo.currentText().split(' (')[0]  # Remove balance from display
            else:
                pay_from_id = None
                pay_from_name = ""
                
            if hasattr(self, 'pay_to_combo'):
                pay_to_id = self.pay_to_combo.currentData()
                pay_to_name = self.pay_to_combo.currentText().split(' (')[0]  # Remove balance from display
                # If it's an editable combo, get the actual text
                if not pay_to_name or pay_to_name == "No loans found" or pay_to_name == "Error loading loans":
                    pay_to_name = self.pay_to_combo.currentText()
            else:
                pay_to_id = None
                pay_to_name = ""
            
            data = {
                'amount': self.amount_spin.value(),
                'desc': self.desc_edit.text().strip(),
                'account': pay_from_name,  # Use pay_from as the main account for compatibility
                'account_id': pay_from_id,
                'pay_from': pay_from_name,
                'pay_from_id': pay_from_id,
                'pay_to': pay_to_name,
                'pay_to_id': pay_to_id,
                'type': 'in' if self.type_combo.currentText() == 'Income' else ('loan_payment' if self.type_combo.currentText() == 'Loan Payment' else 'out'),
                'category': self.category_combo.currentText(),
                'frequency': self.frequency_combo.currentText(),
                'start_date': self.start_date.date().toString('yyyy-MM-dd'),
                'end_date': None if self.indefinite_check.isChecked() else self.end_date.date().toString('yyyy-MM-dd')
            }
        else:
            # For regular transactions, use the original account field
            if hasattr(self, 'account_combo'):
                account_id = self.account_combo.currentData()
                account_name = self.account_combo.currentText().split(' (')[0]  # Remove balance from display
            else:
                account_id = None
                account_name = self.account_edit.text().strip()
            
            data = {
                'amount': self.amount_spin.value(),
                'desc': self.desc_edit.text().strip(),
                'account': account_name,
                'account_id': account_id,
                'type': 'in' if self.type_combo.currentText() == 'Income' else ('loan_payment' if self.type_combo.currentText() == 'Loan Payment' else 'out'),
                'category': self.category_combo.currentText(),
                'splits': self.splits_data if hasattr(self, 'splits_data') and self.splits_data else None,
                'attachments': self.attachments_data if hasattr(self, 'attachments_data') and self.attachments_data else None
            }
        
        return data
    
    def on_split_checkbox_changed(self, state):
        """Handle split transaction checkbox state changes"""
        if not hasattr(self, 'split_edit_btn'):
            return
        
        is_checked = (state == Qt.CheckState.Checked.value)
        self.split_edit_btn.setEnabled(is_checked)
        self.category_combo.setEnabled(not is_checked)
        
        if not is_checked:
            # Clear splits if unchecking
            self.splits_data = []
            self.update_split_summary()
        else:
            # Open split dialog if checking
            self.open_split_dialog()
    
    def open_split_dialog(self):
        """Open the split transaction dialog"""
        if not hasattr(self, 'category_combo'):
            return
        
        # Get available categories from the combo box
        categories = [self.category_combo.itemText(i) for i in range(self.category_combo.count())]
        
        # Get current transaction amount
        amount = self.amount_spin.value()
        
        if amount <= 0:
            QMessageBox.warning(self, 'Invalid Amount', 'Please enter a transaction amount before splitting')
            if hasattr(self, 'split_checkbox'):
                self.split_checkbox.setChecked(False)
            return
        
        # Open split dialog
        dialog = SplitTransactionDialog(
            self,
            total_amount=amount,
            existing_splits=self.splits_data,
            categories=categories
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.splits_data = dialog.get_splits()
            self.update_split_summary()
        else:
            # If cancelled and no splits exist, uncheck the box
            if not self.splits_data and hasattr(self, 'split_checkbox'):
                self.split_checkbox.setChecked(False)
    
    def update_split_summary(self):
        """Update the split summary label"""
        if not hasattr(self, 'split_summary_label'):
            return
        
        if not self.splits_data:
            self.split_summary_label.setText('')
            return
        
        # Create summary text
        summary_parts = []
        for split in self.splits_data:
            summary_parts.append(f"{split['category']}: ${split['amount']:.2f}")
        
        summary_text = f"Split into {len(self.splits_data)} categories: " + ", ".join(summary_parts)
        self.split_summary_label.setText(summary_text)
    
    def add_attachment(self):
        """Open file picker to add an attachment"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Select Attachment',
            '',
            'All Files (*);;Images (*.png *.jpg *.jpeg *.gif *.bmp);;PDFs (*.pdf);;Documents (*.doc *.docx *.txt *.csv)'
        )
        
        if file_path:
            try:
                # Add attachment using attachment manager
                attachment_data = self.attachment_manager.add_attachment(file_path)
                self.attachments_data.append(attachment_data)
                self.refresh_attachments_list()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to add attachment:\n{e}')
    
    def remove_attachment(self, index):
        """Remove an attachment"""
        if 0 <= index < len(self.attachments_data):
            attachment = self.attachments_data[index]
            
            reply = QMessageBox.question(
                self,
                'Confirm Delete',
                f'Remove attachment "{attachment["filename"]}"?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Delete the file
                self.attachment_manager.delete_attachment(attachment)
                # Remove from list
                self.attachments_data.pop(index)
                self.refresh_attachments_list()
    
    def view_attachment(self, index):
        """View an attachment"""
        if 0 <= index < len(self.attachments_data):
            dialog = AttachmentViewerDialog(
                self,
                attachments=self.attachments_data,
                current_index=index,
                attachment_manager=self.attachment_manager
            )
            dialog.exec()
    
    def refresh_attachments_list(self):
        """Refresh the attachments list table"""
        if not hasattr(self, 'attachments_list'):
            return
        
        self.attachments_list.setRowCount(len(self.attachments_data))
        
        for row, attachment in enumerate(self.attachments_data):
            # Icon
            file_type = attachment.get('type', '')
            icon = self.attachment_manager.get_file_icon(file_type)
            icon_item = QTableWidgetItem(icon)
            icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.attachments_list.setItem(row, 0, icon_item)
            
            # Filename
            filename = attachment.get('filename', 'Unknown')
            filename_item = QTableWidgetItem(filename)
            self.attachments_list.setItem(row, 1, filename_item)
            
            # Size
            file_size = attachment.get('size', 0)
            size_str = self.attachment_manager.format_file_size(file_size)
            size_item = QTableWidgetItem(size_str)
            self.attachments_list.setItem(row, 2, size_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 0, 4, 0)
            
            view_btn = QPushButton('View')
            view_btn.clicked.connect(lambda checked, idx=row: self.view_attachment(idx))
            actions_layout.addWidget(view_btn)
            
            delete_btn = QPushButton('Delete')
            delete_btn.clicked.connect(lambda checked, idx=row: self.remove_attachment(idx))
            actions_layout.addWidget(delete_btn)
            
            self.attachments_list.setCellWidget(row, 3, actions_widget)

class CombineFinancesDialog(QDialog):
    def __init__(self, parent=None, current_user_id=None):
        super().__init__(parent)
        self.current_user_id = current_user_id
        self.setWindowTitle('Combine Finances')
        self.setMinimumWidth(350)
        
        layout = QFormLayout()
        
        # Load available users
        self.account_manager = AccountManager()
        users = list(self.account_manager.accounts.keys())
        
        # Remove current user from list
        if current_user_id in users:
            users.remove(current_user_id)
        
        self.user_combo = QComboBox()
        self.user_combo.addItems(users)
        layout.addRow('Combine finances with:', self.user_combo)
        
        info_label = QLabel('This will allow both users to see each other\'s financial transactions.')
        info_label.setWordWrap(True)
        layout.addRow('', info_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_selected_user(self):
        return self.user_combo.currentText()

class AddLoanDialog(QDialog):
    """Dialog to add a new loan tracked separately from income/expenses."""
    def __init__(self, parent=None, bank: Bank | None = None, current_user_id=None):
        super().__init__(parent)
        self.bank = bank
        self.current_user_id = current_user_id
        self.setWindowTitle('Add Loan')
        self.setMinimumWidth(420)

        layout = QFormLayout()

        # Description
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText('e.g., Car Loan, Mortgage, Personal Loan')
        layout.addRow('Description:', self.desc_edit)

        # Principal
        self.principal_spin = QDoubleSpinBox()
        self.principal_spin.setDecimals(2)
        self.principal_spin.setMaximum(1_000_000_000.00)
        self.principal_spin.setPrefix('$')
        layout.addRow('Principal:', self.principal_spin)

        # Annual Interest Rate
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setDecimals(3)
        self.rate_spin.setSuffix(' %')
        self.rate_spin.setMaximum(100.0)
        layout.addRow('Annual Rate:', self.rate_spin)

        # Minimum Payment (per period)
        self.payment_spin = QDoubleSpinBox()
        self.payment_spin.setDecimals(2)
        self.payment_spin.setMaximum(1_000_000.00)
        self.payment_spin.setPrefix('$')
        layout.addRow('Minimum Payment:', self.payment_spin)

        # Loan Account Creation Options
        account_group = QGroupBox("Loan Account Setup")
        account_layout = QFormLayout()
        
        # Auto-create option (default and recommended)
        self.auto_create_check = QCheckBox('Auto-create loan account (Recommended)')
        self.auto_create_check.setChecked(True)
        self.auto_create_check.setToolTip('Automatically creates a loan account for tracking this loan.')
        account_layout.addRow('', self.auto_create_check)
        
        # Manual account selection (for advanced users)
        self.manual_account_check = QCheckBox('Use existing account (Advanced)')
        self.manual_account_check.setToolTip('Select an existing account to associate with this loan.')
        account_layout.addRow('', self.manual_account_check)
        
        self.account_combo = QComboBox()
        self.account_combo.addItem('Select existing account...', None)
        self.account_combo.setEnabled(False)  # Disabled by default
        try:
            if self.bank:
                for info in self.bank.get_accounts_summary(self.current_user_id):
                    display = info['display_name']
                    self.account_combo.addItem(display, info['account_id'])
        except Exception as e:
            logger.warning("AddLoanDialog", f"Failed to load accounts: {e}")
        account_layout.addRow('Existing Account:', self.account_combo)
        
        # Connect checkbox signals
        self.auto_create_check.toggled.connect(self.on_auto_create_toggled)
        self.manual_account_check.toggled.connect(self.on_manual_account_toggled)
        
        account_group.setLayout(account_layout)
        layout.addRow(account_group)

        # Pay From Account selector (cannot be loan accounts)
        self.pay_from_combo = QComboBox()
        self.pay_from_combo.addItem('Select Payment Account', None)
        try:
            if self.bank:
                for info in self.bank.get_accounts_summary(self.current_user_id):
                    display = info['display_name']
                    account_type = info.get('account_type', '').lower()
                    # Exclude loan accounts from payment source options
                    if 'loan' not in account_type:
                        self.pay_from_combo.addItem(display, info['account_id'])
        except Exception as e:
            logger.warning("AddLoanDialog", f"Failed to load payment accounts: {e}")
        layout.addRow('Pay From Account:', self.pay_from_combo)

        # Frequency
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(['weekly', 'monthly', 'yearly'])
        layout.addRow('Frequency:', self.frequency_combo)

        # Start/End dates
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        layout.addRow('Start Date:', self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addYears(1))
        layout.addRow('End Date (Optional):', self.end_date)

        self.indefinite_check = QCheckBox('Indefinite (no end date)')
        layout.addRow('', self.indefinite_check)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def on_auto_create_toggled(self, checked):
        """Handle auto-create checkbox toggle"""
        if checked:
            self.manual_account_check.setChecked(False)
            self.account_combo.setEnabled(False)
    
    def on_manual_account_toggled(self, checked):
        """Handle manual account checkbox toggle"""
        if checked:
            self.auto_create_check.setChecked(False)
            self.account_combo.setEnabled(True)
        else:
            self.account_combo.setEnabled(False)

    def get_data(self):
        # Handle account selection based on user choice
        if self.auto_create_check.isChecked():
            # Auto-create account - don't provide account info
            account_id = None
            account_name = None
            auto_create_account = True
        else:
            # Use existing account
            account_id = self.account_combo.currentData()
            account_name = self.account_combo.currentText() if account_id else None
            auto_create_account = False
            
        pay_from_account_id = self.pay_from_combo.currentData()
        pay_from_account_name = self.pay_from_combo.currentText() if pay_from_account_id else None
        return {
            'desc': self.desc_edit.text().strip(),
            'principal': float(self.principal_spin.value()),
            'annual_rate': float(self.rate_spin.value()) / 100.0,  # convert % -> decimal
            'minimum_payment': float(self.payment_spin.value()),
            'payment_amount': float(self.payment_spin.value()),  # Keep for backward compatibility
            'account_id': account_id,
            'account_name': account_name,
            'auto_create_account': auto_create_account,
            'pay_from_account_id': pay_from_account_id,
            'pay_from_account_name': pay_from_account_name if pay_from_account_id else None,
            'frequency': self.frequency_combo.currentText(),
            'start_date': self.start_date.date().toString('yyyy-MM-dd'),
            'end_date': None if self.indefinite_check.isChecked() else self.end_date.date().toString('yyyy-MM-dd'),
        }

class FinancialTracker(QWidget):
    def __init__(self, current_user_id=None):
        super().__init__()
        print(f"[DEBUG] FinancialTracker.__init__: Initializing for user: {current_user_id}")
        logger.debug("FinancialTracker", f"Initializing for user: {current_user_id}")
        try:
            self.current_user_id = current_user_id
            self._signal_processing = False  # Flag to prevent recursive signal calls
            print("[DEBUG] FinancialTracker.__init__: Creating Bank instance...")
            self.bank = Bank(current_user_id)
            print("[DEBUG] FinancialTracker.__init__: Bank instance created")
            
            print("[DEBUG] FinancialTracker.__init__: Creating AccountManager...")
            self.account_manager = AccountManager()
            print("[DEBUG] FinancialTracker.__init__: AccountManager created")
            
            print("[DEBUG] FinancialTracker.__init__: Creating BudgetManager...")
            self.budget_manager = BudgetManager(current_user_id)
            print("[DEBUG] FinancialTracker.__init__: BudgetManager created")
            
            print("[DEBUG] FinancialTracker.__init__: Creating RuleManager...")
            self.rule_manager = RuleManager()
            print("[DEBUG] FinancialTracker.__init__: RuleManager created")
            
            print("[DEBUG] FinancialTracker.__init__: Creating GoalManager...")
            self.goal_manager = GoalManager()
            print("[DEBUG] FinancialTracker.__init__: GoalManager created")
            
            print("[DEBUG] FinancialTracker.__init__: Creating NetWorthTracker...")
            self.net_worth_tracker = NetWorthTracker()
            print("[DEBUG] FinancialTracker.__init__: NetWorthTracker created")
            
            print("[DEBUG] FinancialTracker.__init__: Creating TagManager...")
            self.tag_manager = TagManager()
            print("[DEBUG] FinancialTracker.__init__: TagManager created")
            
            print("[DEBUG] FinancialTracker.__init__: Setting up UI...")
            self.setup_ui()
            print("[DEBUG] FinancialTracker.__init__: UI setup completed")
            
            print("[DEBUG] FinancialTracker.__init__: Refreshing data...")
            try:
                self.refresh_data()
            except KeyboardInterrupt:
                logger.error("FinancialTracker", "Data refresh interrupted, continuing with empty data")
            except Exception as e:
                logger.error("FinancialTracker", f"Error during data refresh: {e}")
            print("[DEBUG] FinancialTracker.__init__: Data refresh completed")
            
            print("[DEBUG] FinancialTracker.__init__: FinancialTracker initialization completed successfully")
            
        except Exception as e:
            print(f"[ERROR] FinancialTracker.__init__: Error during initialization: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise to let caller handle it
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Financial Tracker')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Create tabs
        tab_widget = QTabWidget()
        
        # Overview Tab
        overview_tab = self.create_overview_tab()
        tab_widget.addTab(overview_tab, 'Overview')
        
        # Transactions Tab
        transactions_tab = self.create_transactions_tab()
        tab_widget.addTab(transactions_tab, 'Transactions')
        
        # Recurring Tab
        recurring_tab = self.create_recurring_tab()
        tab_widget.addTab(recurring_tab, 'Recurring')
        
        # Loans Tab
        loans_tab = self.create_loans_tab()
        tab_widget.addTab(loans_tab, 'Loans')
        
        # Budget Tab
        budget_tab = self.create_budget_tab()
        tab_widget.addTab(budget_tab, 'Budgets')
        
        # Goals Tab
        goals_tab = self.create_goals_tab()
        tab_widget.addTab(goals_tab, '🎯 Goals')
        
        # Net Worth Tab
        net_worth_tab = self.create_net_worth_tab()
        tab_widget.addTab(net_worth_tab, '💰 Net Worth')
        
        # Stock Manager Tab
        stock_manager_tab = self.create_stock_manager_tab()
        tab_widget.addTab(stock_manager_tab, '📈 Stocks')
        
        # Banking API Tab
        banking_api_tab = self.create_banking_api_tab()
        tab_widget.addTab(banking_api_tab, '🏦 Banking API')
        
        # Bank Dashboards Tab
        bank_dashboards_tab = self.create_bank_dashboards_tab()
        tab_widget.addTab(bank_dashboards_tab, 'Bank Dashboards')
        
        # Settings Tab
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, 'Settings')
        
        layout.addWidget(tab_widget)
        self.setLayout(layout)
        
        # Set up delegates after all tables are created
        self.setup_all_table_delegates()
    
    def setup_all_table_delegates(self):
        """Set up delegates for all tables after UI is fully created"""
        print("[DEBUG] setup_all_table_delegates: Setting up delegates for all tables...")
        try:
            # Check if all required tables exist before setting up delegates
            if hasattr(self, 'transactions_table'):
                print("[DEBUG] setup_all_table_delegates: Setting up transactions table delegates...")
                self.setup_table_delegates()
            else:
                print("[WARNING] setup_all_table_delegates: transactions_table not found")
            
            if hasattr(self, 'recurring_table'):
                print("[DEBUG] setup_all_table_delegates: Setting up recurring table delegates...")
                self.setup_recurring_table_delegates()
            else:
                print("[WARNING] setup_all_table_delegates: recurring_table not found")
            
            if hasattr(self, 'loans_table'):
                print("[DEBUG] setup_all_table_delegates: Setting up loans table delegates...")
                self.setup_loans_table_delegates()
            else:
                print("[WARNING] setup_all_table_delegates: loans_table not found")
                
            print("[DEBUG] setup_all_table_delegates: All delegate setup completed")
        except Exception as e:
            print(f"[ERROR] setup_all_table_delegates: Error setting up delegates: {e}")
            import traceback
            traceback.print_exc()
    
    def create_overview_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Summary cards
        summary_layout = QHBoxLayout()
        
        self.income_label = QLabel('Total Income: $0.00')
        self.income_label.setStyleSheet('font-size: 14px; font-weight: bold; color: green;')
        summary_layout.addWidget(self.income_label)
        
        self.expense_label = QLabel('Total Expenses: $0.00')
        self.expense_label.setStyleSheet('font-size: 14px; font-weight: bold; color: red;')
        summary_layout.addWidget(self.expense_label)
        
        self.balance_label = QLabel('Net Balance: $0.00')
        self.balance_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        summary_layout.addWidget(self.balance_label)
        
        layout.addLayout(summary_layout)
        
        # Charts
        chart_layout = QHBoxLayout()
        
        # Income vs Expenses chart
        self.overview_chart = FigureCanvas(Figure(figsize=(6, 4)))
        chart_layout.addWidget(self.overview_chart)
        
        # Category breakdown chart
        self.category_chart = FigureCanvas(Figure(figsize=(6, 4)))
        chart_layout.addWidget(self.category_chart)
        
        layout.addLayout(chart_layout)
        
        # Upcoming Payments Section
        upcoming_group = QGroupBox("Upcoming Payments (Next 30 Days)")
        upcoming_layout = QVBoxLayout()
        
        self.upcoming_table = QTableWidget()
        self.upcoming_table.setColumnCount(4)
        self.upcoming_table.setHorizontalHeaderLabels(['Description', 'Amount', 'Due Date', 'Category'])
        header = self.upcoming_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.upcoming_table.setMaximumHeight(150)
        
        upcoming_layout.addWidget(self.upcoming_table)
        upcoming_group.setLayout(upcoming_layout)
        layout.addWidget(upcoming_group)
        
        # Overdue Payments Section
        overdue_group = QGroupBox("Overdue Payments")
        overdue_group.setStyleSheet("QGroupBox::title { color: red; font-weight: bold; }")
        overdue_layout = QVBoxLayout()
        
        self.overdue_table = QTableWidget()
        self.overdue_table.setColumnCount(5)
        self.overdue_table.setHorizontalHeaderLabels(['Description', 'Amount', 'Due Date', 'Days Late', 'Category'])
        header = self.overdue_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.overdue_table.setMaximumHeight(120)
        
        overdue_layout.addWidget(self.overdue_table)
        overdue_group.setLayout(overdue_layout)
        layout.addWidget(overdue_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_transactions_tab(self):
        print("[DEBUG] creating Transactions tab...")
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        add_btn = QPushButton('Add Transaction')
        add_btn.clicked.connect(self.add_transaction)
        controls_layout.addWidget(add_btn)
        
        # Process recurring button
        process_btn = QPushButton('Process Recurring Transactions')
        process_btn.clicked.connect(self.process_recurring)
        controls_layout.addWidget(process_btn)
        
        controls_layout.addStretch()
        
        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Search transactions...')
        self.search_edit.textChanged.connect(self.filter_transactions)
        controls_layout.addWidget(self.search_edit)
        
        layout.addLayout(controls_layout)
        
        # Advanced Filters
        filters_group = QGroupBox("Transaction Filters")
        filters_layout = QGridLayout()
        
        # Date Range Filter
        filters_layout.addWidget(QLabel("Date Range:"), 0, 0)
        self.filter_start_date = QDateEdit()
        self.filter_start_date.setDate(QDate.currentDate().addDays(-30))  # Default to last 30 days
        self.filter_start_date.setCalendarPopup(True)
        self.filter_start_date.dateChanged.connect(self.filter_transactions)
        filters_layout.addWidget(self.filter_start_date, 0, 1)
        
        filters_layout.addWidget(QLabel("to"), 0, 2)
        self.filter_end_date = QDateEdit()
        self.filter_end_date.setDate(QDate.currentDate())
        self.filter_end_date.setCalendarPopup(True)
        self.filter_end_date.dateChanged.connect(self.filter_transactions)
        filters_layout.addWidget(self.filter_end_date, 0, 3)
        
        # Amount Range Filter
        filters_layout.addWidget(QLabel("Amount Range:"), 1, 0)
        self.filter_min_amount = QDoubleSpinBox()
        self.filter_min_amount.setPrefix("$")
        self.filter_min_amount.setMinimum(0.0)
        self.filter_min_amount.setMaximum(999999.99)
        self.filter_min_amount.setValue(0.0)
        self.filter_min_amount.valueChanged.connect(self.filter_transactions)
        filters_layout.addWidget(self.filter_min_amount, 1, 1)
        
        filters_layout.addWidget(QLabel("to"), 1, 2)
        self.filter_max_amount = QDoubleSpinBox()
        self.filter_max_amount.setPrefix("$")
        self.filter_max_amount.setMinimum(0.0)
        self.filter_max_amount.setMaximum(999999.99)
        self.filter_max_amount.setValue(999999.99)
        self.filter_max_amount.valueChanged.connect(self.filter_transactions)
        filters_layout.addWidget(self.filter_max_amount, 1, 3)
        
        # Type Filter
        filters_layout.addWidget(QLabel("Type:"), 2, 0)
        self.filter_type = QComboBox()
        self.filter_type.addItems(["All Types", "Income", "Expense", "Loan Payment"])
        self.filter_type.currentTextChanged.connect(self.filter_transactions)
        filters_layout.addWidget(self.filter_type, 2, 1)
        
        # Account Filter
        filters_layout.addWidget(QLabel("Account:"), 2, 2)
        self.filter_account = QComboBox()
        self.filter_account.addItem("All Accounts")
        self.filter_account.currentTextChanged.connect(self.filter_transactions)
        filters_layout.addWidget(self.filter_account, 2, 3)
        
        # Category Filter
        filters_layout.addWidget(QLabel("Category:"), 3, 0)
        self.filter_category = QComboBox()
        self.filter_category.addItem("All Categories")
        self.filter_category.currentTextChanged.connect(self.filter_transactions)
        filters_layout.addWidget(self.filter_category, 3, 1)
        
        # Bank Filter
        filters_layout.addWidget(QLabel("Bank:"), 3, 2)
        self.filter_bank = QComboBox()
        self.filter_bank.addItem("All Banks")
        self.filter_bank.currentTextChanged.connect(self.filter_transactions)
        filters_layout.addWidget(self.filter_bank, 3, 3)
        
        # Filter buttons
        filter_buttons_layout = QHBoxLayout()
        
        clear_filters_btn = QPushButton("Clear Filters")
        clear_filters_btn.clicked.connect(self.clear_filters)
        filter_buttons_layout.addWidget(clear_filters_btn)
        
        export_filtered_btn = QPushButton("Export Filtered")
        export_filtered_btn.clicked.connect(self.export_filtered_transactions)
        filter_buttons_layout.addWidget(export_filtered_btn)
        
        filter_buttons_layout.addStretch()
        
        # Filter summary
        self.filter_summary_label = QLabel("Showing all transactions")
        self.filter_summary_label.setStyleSheet("color: #666; font-style: italic;")
        filter_buttons_layout.addWidget(self.filter_summary_label)
        
        filters_layout.addLayout(filter_buttons_layout, 4, 0, 1, 4)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # Transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(8)
        self.transactions_table.setHorizontalHeaderLabels([
            'Date', 'Description*', 'Category*', 'Account*', 'Type*', 'Amount*', '📎', 'Actions'
        ])
        header = self.transactions_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            # Set fixed width for attachment column
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
            self.transactions_table.setColumnWidth(6, 40)
        
        # Add tooltip to explain editable columns
        self.transactions_table.setToolTip("Columns marked with * are editable. Use dropdowns for easy selection.")
        
        # Re-enable table editing with proper error handling
        print("[DEBUG] create_transactions_tab: Re-enabling table editing with error handling...")
        self.transactions_table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked | 
            QTableWidget.EditTrigger.EditKeyPressed |
            QTableWidget.EditTrigger.AnyKeyPressed
        )
        print("[DEBUG] create_transactions_tab: Table editing re-enabled")
        
        # Store original transaction data for modification tracking
        self.original_transactions = {}
        
        # Re-enable delegate setup with error handling
        print("[DEBUG] create_transactions_tab: Deferring delegate setup until all tables are created...")
        print("[DEBUG] create_transactions_tab: Delegates will be setup after UI initialization")
        
        # Defer signal connection; we'll connect in update_transactions_table after population
        print("[DEBUG] create_transactions_tab: Deferring cell change signal connection to update step")
        # try:
        #     self.transactions_table.itemChanged.connect(self.on_transaction_cell_changed)
        #     print("[DEBUG] create_transactions_tab: Signal connected successfully")
        # except Exception as e:
        #     print(f"[ERROR] create_transactions_tab: Failed to connect signal: {e}")
        #     import traceback
        #     traceback.print_exc()
        
        # Add debugging for table interactions
        print("[DEBUG] create_transactions_tab: Setting up table event debugging...")
        try:
            self.transactions_table.itemDoubleClicked.connect(
                lambda item: print(f"[DEBUG] Table: Item double-clicked at row {item.row()}, col {item.column()}")
            )
            self.transactions_table.itemClicked.connect(
                lambda item: print(f"[DEBUG] Table: Item clicked at row {item.row()}, col {item.column()}")
            )
            self.transactions_table.itemSelectionChanged.connect(
                lambda: print("[DEBUG] Table: Selection changed")
            )
            print("[DEBUG] create_transactions_tab: Table event debugging connected")
        except Exception as e:
            print(f"[ERROR] create_transactions_tab: Failed to connect table debugging: {e}")
            import traceback
            traceback.print_exc()
        
        layout.addWidget(self.transactions_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_recurring_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        add_recurring_btn = QPushButton('Add Recurring Transaction')
        add_recurring_btn.clicked.connect(self.add_recurring_transaction)
        controls_layout.addWidget(add_recurring_btn)
        
        calendar_preview_btn = QPushButton('📅 Calendar Preview')
        calendar_preview_btn.clicked.connect(self.show_recurring_calendar)
        controls_layout.addWidget(calendar_preview_btn)
        
        notifications_btn = QPushButton('🔔 Upcoming (Next 7 Days)')
        notifications_btn.clicked.connect(self.show_upcoming_recurring)
        controls_layout.addWidget(notifications_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Recurring transactions table
        self.recurring_table = QTableWidget()
        self.recurring_table.setColumnCount(10)
        self.recurring_table.setHorizontalHeaderLabels([
            'Description', 'Category', 'Account', 'Type', 'Amount', 'Frequency', 'Status', 'Next Due', 'Instances', 'Actions'
        ])
        header = self.recurring_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Enable editing for specific columns only
        self.recurring_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        # Connect signal for cell changes
        self.recurring_table.cellChanged.connect(self.on_recurring_cell_changed)
        layout.addWidget(self.recurring_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_goals_tab(self):
        """Create the Goals tab UI with goal cards and progress tracking"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        title_label = QLabel('🎯 Savings Goals')
        title_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        add_goal_btn = QPushButton('➕ Add Goal')
        add_goal_btn.clicked.connect(self.add_goal)
        add_goal_btn.setStyleSheet('QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px; }')
        header_layout.addWidget(add_goal_btn)
        
        stats_btn = QPushButton('📊 Statistics')
        stats_btn.clicked.connect(self.show_goal_statistics)
        header_layout.addWidget(stats_btn)
        
        layout.addLayout(header_layout)
        
        # Goals scroll area with cards
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; }')
        
        self.goals_container = QWidget()
        self.goals_layout = QVBoxLayout(self.goals_container)
        self.goals_layout.setSpacing(15)
        
        scroll.setWidget(self.goals_container)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_net_worth_tab(self):
        """Create Net Worth tracking tab with trends and visualizations"""
        from PyQt6.QtWidgets import QScrollArea
        
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        title = QLabel('Net Worth Tracking')
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Take Snapshot button
        snapshot_btn = QPushButton('📸 Take Snapshot')
        snapshot_btn.clicked.connect(self.take_net_worth_snapshot)
        header_layout.addWidget(snapshot_btn)
        
        # View History button
        history_btn = QPushButton('📜 View History')
        history_btn.clicked.connect(self.view_net_worth_history)
        header_layout.addWidget(history_btn)
        
        # Export button
        export_btn = QPushButton('📊 Export CSV')
        export_btn.clicked.connect(self.export_net_worth)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container for net worth displays
        self.net_worth_container = QWidget()
        self.net_worth_layout = QVBoxLayout(self.net_worth_container)
        self.net_worth_layout.setSpacing(15)
        
        scroll.setWidget(self.net_worth_container)
        layout.addWidget(scroll)
        
        widget.setLayout(layout)
        return widget
    
    def create_stock_manager_tab(self):
        """Create Stock Manager tab with watchlist and portfolio"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create the stock manager widget
        self.stock_manager_widget = StockManagerWidget(
            username=self.current_user_id,
            parent=self
        )
        
        # Connect signals if needed
        self.stock_manager_widget.symbol_selected.connect(self.on_stock_symbol_selected)
        
        layout.addWidget(self.stock_manager_widget)
        widget.setLayout(layout)
        return widget
    
    def on_stock_symbol_selected(self, symbol):
        """Handle stock symbol selection"""
        # You can implement additional behavior here, such as:
        # - Opening a detailed chart view
        # - Showing news for the symbol
        # - Displaying fundamental data
        print(f"Stock symbol selected: {symbol}")
        # For now, just show a message
        QMessageBox.information(
            self,
            f"{symbol} Selected",
            f"You selected {symbol}.\n\n"
            "Feature coming soon:\n"
            "- Detailed charts\n"
            "- Company information\n"
            "- News feed\n"
            "- Technical analysis"
        )
    
    def create_banking_api_tab(self):
        """Create Banking API integration tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create the banking API widget
        self.banking_api_widget = BankingAPIWidget(
            bank_instance=self.bank,
            user_id=self.current_user_id,
            parent=self
        )
        
        layout.addWidget(self.banking_api_widget)
        widget.setLayout(layout)
        return widget
    
    def create_bank_dashboards_tab(self):
        """Create bank-specific dashboard tab with different visualizations based on account types"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Bank selection and info
        header_layout = QHBoxLayout()
        
        header_layout.addWidget(QLabel("Select Bank:"))
        self.bank_selector = QComboBox()
        self.bank_selector.currentTextChanged.connect(self.update_bank_dashboard)
        header_layout.addWidget(self.bank_selector)
        
        refresh_banks_btn = QPushButton("Refresh Banks")
        refresh_banks_btn.clicked.connect(self.populate_bank_selector)
        header_layout.addWidget(refresh_banks_btn)
        
        header_layout.addStretch()
        
        self.bank_info_label = QLabel("Select a bank to view dashboard")
        self.bank_info_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        header_layout.addWidget(self.bank_info_label)
        
        layout.addLayout(header_layout)
        
        # Bank dashboard content area
        self.bank_dashboard_widget = QWidget()
        self.bank_dashboard_layout = QVBoxLayout()
        self.bank_dashboard_layout.setSpacing(25)  # Moderate spacing - reduced from 50px back to 25px
        self.bank_dashboard_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins back to 10px
        self.bank_dashboard_widget.setLayout(self.bank_dashboard_layout)
        self.bank_dashboard_widget.setMinimumHeight(1000)  # Force content to be tall enough for scrolling
        
        # Scroll area for dashboard content
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(500)  # Reasonable scroll area height
        scroll_area.setMaximumHeight(700)  # Limit scroll area to force scrolling
        scroll_area.setWidget(self.bank_dashboard_widget)
        
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        
        # Initialize bank selector
        self.populate_bank_selector()
        
        return widget
    
    def populate_bank_selector(self):
        """Populate the bank selector with available banks"""
        try:
            current_selection = self.bank_selector.currentText()
            self.bank_selector.clear()
            
            # Get all accounts and extract unique bank names
            accounts_summary = self.bank.get_accounts_summary(self.current_user_id)
            banks = set()
            
            for account_info in accounts_summary:
                bank_name = account_info.get('bank_name', 'Unknown Bank')
                if bank_name and bank_name.strip():
                    banks.add(bank_name)
            
            if banks:
                for bank in sorted(banks):
                    self.bank_selector.addItem(bank)
                
                # Restore previous selection if still valid
                index = self.bank_selector.findText(current_selection)
                if index >= 0:
                    self.bank_selector.setCurrentIndex(index)
                else:
                    self.bank_selector.setCurrentIndex(0)
            else:
                self.bank_selector.addItem("No banks found")
                
        except Exception as e:
            print(f"[ERROR] Error populating bank selector: {e}")
            self.bank_selector.addItem("Error loading banks")
    
    def update_bank_dashboard(self):
        """Update the dashboard for the selected bank"""
        selected_bank = self.bank_selector.currentText()
        if not selected_bank or selected_bank in ["No banks found", "Error loading banks"]:
            return
            
        try:
            # Clear existing dashboard content
            for i in reversed(range(self.bank_dashboard_layout.count())):
                item = self.bank_dashboard_layout.itemAt(i)
                if item is not None:
                    child = item.widget()
                    if child:
                        child.deleteLater()
            
            # Get accounts for this bank
            accounts_summary = self.bank.get_accounts_summary(self.current_user_id)
            bank_accounts = [acc for acc in accounts_summary if acc.get('bank_name') == selected_bank]
            
            if not bank_accounts:
                no_accounts_label = QLabel(f"No accounts found for {selected_bank}")
                no_accounts_label.setStyleSheet("color: #999; font-style: italic; padding: 20px;")
                self.bank_dashboard_layout.addWidget(no_accounts_label)
                return
            
            # Update bank info
            total_balance = sum(acc['balance'] for acc in bank_accounts)
            self.bank_info_label.setText(f"{selected_bank} - {len(bank_accounts)} accounts - Total: ${total_balance:,.2f}")
            
            # Create dashboard based on account types
            self.create_bank_summary_section(selected_bank, bank_accounts)
            self.create_account_breakdown_section(bank_accounts)
            self.create_bank_charts_section(selected_bank, bank_accounts)
            self.create_recent_transactions_section(selected_bank, bank_accounts)
            
            # Add spacer at bottom to ensure scrolling
            self.bank_dashboard_layout.addStretch()
            
            # Add some bottom padding
            bottom_spacer = QLabel(" ")
            bottom_spacer.setMinimumHeight(80)  # Reduced from 150px to 80px for reasonable bottom space
            self.bank_dashboard_layout.addWidget(bottom_spacer)
            
        except Exception as e:
            print(f"[ERROR] Error updating bank dashboard: {e}")
            error_label = QLabel(f"Error loading dashboard for {selected_bank}: {e}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            self.bank_dashboard_layout.addWidget(error_label)
    
    def create_bank_summary_section(self, bank_name, accounts):
        """Create summary section for the bank"""
        summary_group = QGroupBox(f"{bank_name} Summary")
        summary_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; padding-top: 10px; }")
        summary_layout = QGridLayout()
        # Remove excessive spacing and margins from summary section
        
        # Account type breakdown
        account_types = {}
        total_balance = 0
        
        for account in accounts:
            acc_type = account['account_type']
            balance = account['balance']
            
            if acc_type not in account_types:
                account_types[acc_type] = {'count': 0, 'balance': 0}
            
            account_types[acc_type]['count'] += 1
            account_types[acc_type]['balance'] += balance
            total_balance += balance
        
        # Display summary stats
        row = 0
        for acc_type, stats in account_types.items():
            type_label = QLabel(f"{acc_type}:")
            type_label.setStyleSheet("font-weight: bold;")
            summary_layout.addWidget(type_label, row, 0)
            
            count_label = QLabel(f"{stats['count']} account{'s' if stats['count'] != 1 else ''}")
            summary_layout.addWidget(count_label, row, 1)
            
            balance_label = QLabel(f"${stats['balance']:,.2f}")
            balance_color = "green" if stats['balance'] >= 0 else "red"
            balance_label.setStyleSheet(f"color: {balance_color}; font-weight: bold;")
            summary_layout.addWidget(balance_label, row, 2)
            
            row += 1
        
        # Total row
        summary_layout.addWidget(QLabel(""), row, 0)  # Spacer
        row += 1
        
        total_label = QLabel("Total:")
        total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(total_label, row, 0)
        
        total_balance_label = QLabel(f"${total_balance:,.2f}")
        total_color = "green" if total_balance >= 0 else "red"
        total_balance_label.setStyleSheet(f"color: {total_color}; font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(total_balance_label, row, 2)
        
        summary_group.setLayout(summary_layout)
        self.bank_dashboard_layout.addWidget(summary_group)
    
    def create_account_breakdown_section(self, accounts):
        """Create detailed account breakdown section"""
        breakdown_group = QGroupBox("Account Details")
        breakdown_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; padding-top: 10px; }")
        breakdown_layout = QVBoxLayout()
        # Remove excessive spacing and margins from breakdown section
        
        # Create table for account details
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
        accounts_table = QTableWidget()
        accounts_table.setColumnCount(4)
        accounts_table.setHorizontalHeaderLabels(['Account Name', 'Type', 'Balance', 'Status'])
        accounts_table.setRowCount(len(accounts))
        
        for row, account in enumerate(accounts):
            # Account name
            name_item = QTableWidgetItem(account['display_name'])
            accounts_table.setItem(row, 0, name_item)
            
            # Account type
            type_item = QTableWidgetItem(account['account_type'])
            accounts_table.setItem(row, 1, type_item)
            
            # Balance
            balance = account['balance']
            balance_item = QTableWidgetItem(f"${balance:,.2f}")
            balance_color = QColor('green') if balance >= 0 else QColor('red')
            balance_item.setForeground(QBrush(balance_color))
            accounts_table.setItem(row, 2, balance_item)
            
            # Status
            status = "Active" if account['account'].active else "Inactive"
            status_item = QTableWidgetItem(status)
            if status == "Active":
                status_item.setForeground(QBrush(QColor('green')))
            else:
                status_item.setForeground(QBrush(QColor('red')))
            accounts_table.setItem(row, 3, status_item)
        
        accounts_table.resizeColumnsToContents()
        accounts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        accounts_table.setMaximumHeight(200)  # Limit height to prevent over-expansion
        
        breakdown_layout.addWidget(accounts_table)
        breakdown_group.setLayout(breakdown_layout)
        self.bank_dashboard_layout.addWidget(breakdown_group)
    
    def create_bank_charts_section(self, bank_name, accounts):
        """Create charts section based on account types"""
        charts_group = QGroupBox(f"{bank_name} Visualizations")
        charts_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; padding-top: 10px; }")
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)  # Reduced back to 15px from 25px
        # Remove excessive margins in charts section
        
        try:
            # Account type distribution pie chart
            account_types = {}
            for account in accounts:
                acc_type = account['account_type']
                balance = abs(account['balance'])  # Use absolute value for visualization
                
                if acc_type not in account_types:
                    account_types[acc_type] = 0
                account_types[acc_type] += balance
            
            if account_types:
                # Create matplotlib figure with reasonable size
                fig = Figure(figsize=(8, 5))  # Reduced from (10, 6) to prevent overcrowding
                fig.tight_layout(pad=2.0)  # Reduced padding
                ax = fig.add_subplot(111)
                
                labels = list(account_types.keys())
                sizes = list(account_types.values())
                colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#C2C2F0']
                
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors[:len(labels)])
                ax.set_title(f'{bank_name} Account Distribution', fontsize=12, fontweight='bold')
                
                canvas = FigureCanvas(fig)
                canvas.setMinimumSize(350, 250)  # Reduced from 400x300
                canvas.setMaximumSize(450, 350)  # Add maximum size to prevent over-expansion
                from PyQt6.QtWidgets import QSizePolicy
                canvas.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
                charts_layout.addWidget(canvas)
            
            # Balance trend chart (if we have transaction history)
            self.create_balance_trend_chart(bank_name, accounts, charts_layout)
            
        except Exception as e:
            print(f"[ERROR] Error creating charts: {e}")
            error_label = QLabel(f"Error creating charts: {e}")
            error_label.setStyleSheet("color: red;")
            charts_layout.addWidget(error_label)
        
        charts_group.setLayout(charts_layout)
        charts_group.setMinimumHeight(400)  # Increased minimum height
        charts_group.setMaximumHeight(500)  # Increased maximum height
        self.bank_dashboard_layout.addWidget(charts_group)
    
    def create_balance_trend_chart(self, bank_name, accounts, layout):
        """Create a balance trend chart for the bank"""
        try:
            # Get recent transactions for this bank
            account_ids = [acc['account_id'] for acc in accounts]
            
            # Get transactions for last 30 days
            all_transactions = self.bank.get_user_finances(self.current_user_id)
            bank_transactions = []
            
            for tx in all_transactions:
                if tx.get('account_id') in account_ids:
                    bank_transactions.append(tx)
            
            if bank_transactions and len(bank_transactions) > 1:
                # Sort transactions by date
                bank_transactions.sort(key=lambda x: x.get('timestamp', ''))
                
                # Calculate running balance
                dates = []
                balances = []
                
                # Start with current total balance
                current_balance = sum(acc['balance'] for acc in accounts)
                
                # Work backwards from recent transactions
                recent_transactions = bank_transactions[-20:]  # Last 20 transactions
                
                for i, tx in enumerate(recent_transactions):
                    try:
                        tx_date = datetime.fromisoformat(tx['timestamp']).date()
                        dates.append(tx_date)
                        balances.append(current_balance)
                        
                        # Adjust balance for previous state (reverse the transaction)
                        if tx['type'] == 'in':
                            current_balance -= tx['amount']
                        else:
                            current_balance += tx['amount']
                    except:
                        continue
                
                if dates and balances:
                    fig = Figure(figsize=(8, 5))  # Reduced from (10, 6) to prevent overcrowding
                    fig.tight_layout(pad=2.0)  # Reduced padding
                    ax = fig.add_subplot(111)
                    
                    ax.plot(dates, balances, marker='o', linewidth=2, markersize=4)
                    ax.set_title(f'{bank_name} Balance Trend', fontsize=12, fontweight='bold')
                    ax.set_xlabel('Date', fontsize=10)
                    ax.set_ylabel('Balance ($)', fontsize=10)
                    ax.grid(True, alpha=0.3)
                    
                    # Format y-axis as currency
                    from matplotlib.ticker import FuncFormatter
                    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'${x:,.0f}'))
                    
                    # Rotate date labels
                    fig.autofmt_xdate()
                    
                    canvas = FigureCanvas(fig)
                    canvas.setMinimumSize(350, 250)  # Reduced from 400x300
                    canvas.setMaximumSize(450, 350)  # Add maximum size to prevent over-expansion
                    from PyQt6.QtWidgets import QSizePolicy
                    canvas.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
                    layout.addWidget(canvas)
                else:
                    no_trend_label = QLabel("Insufficient transaction data for trend chart")
                    no_trend_label.setStyleSheet("color: #999; font-style: italic;")
                    layout.addWidget(no_trend_label)
            else:
                no_data_label = QLabel("No transaction history for trend analysis")
                no_data_label.setStyleSheet("color: #999; font-style: italic;")
                layout.addWidget(no_data_label)
                
        except Exception as e:
            print(f"[ERROR] Error creating balance trend chart: {e}")
    
    def create_recent_transactions_section(self, bank_name, accounts):
        """Create recent transactions section for the bank"""
        transactions_group = QGroupBox(f"Recent {bank_name} Transactions")
        transactions_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; padding-top: 10px; }")
        transactions_layout = QVBoxLayout()
        # Remove excessive spacing and margins from transactions section
        
        try:
            # Get recent transactions for this bank
            account_ids = [acc['account_id'] for acc in accounts]
            all_transactions = self.bank.get_user_finances(self.current_user_id)
            
            bank_transactions = []
            for tx in all_transactions:
                if tx.get('account_id') in account_ids:
                    bank_transactions.append(tx)
            
            # Sort by date (most recent first)
            bank_transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Show last 10 transactions
            recent_transactions = bank_transactions[:10]
            
            if recent_transactions:
                # Create table
                recent_table = QTableWidget()
                recent_table.setColumnCount(5)
                recent_table.setHorizontalHeaderLabels(['Date', 'Description', 'Account', 'Type', 'Amount'])
                recent_table.setRowCount(len(recent_transactions))
                
                for row, tx in enumerate(recent_transactions):
                    # Date
                    date_str = datetime.fromisoformat(tx['timestamp']).strftime('%Y-%m-%d')
                    recent_table.setItem(row, 0, QTableWidgetItem(date_str))
                    
                    # Description
                    recent_table.setItem(row, 1, QTableWidgetItem(tx.get('desc', 'N/A')))
                    
                    # Account
                    account_name = tx.get('account', 'Unknown')
                    recent_table.setItem(row, 2, QTableWidgetItem(account_name))
                    
                    # Type
                    tx_type = tx.get('type', 'unknown')
                    if tx_type == 'in':
                        type_display = 'Income'
                    elif tx_type == 'loan_payment':
                        type_display = 'Loan Payment'
                    else:
                        type_display = 'Expense'
                    recent_table.setItem(row, 3, QTableWidgetItem(type_display))
                    
                    # Amount
                    amount = tx.get('amount', 0)
                    amount_item = QTableWidgetItem(f"${amount:,.2f}")
                    if tx_type == 'in':
                        amount_item.setForeground(QBrush(QColor('green')))
                    else:
                        amount_item.setForeground(QBrush(QColor('red')))
                    recent_table.setItem(row, 4, amount_item)
                
                recent_table.resizeColumnsToContents()
                recent_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
                recent_table.setMinimumHeight(250)  # Increased minimum height
                recent_table.setMaximumHeight(500)  # Increased maximum height
                
                transactions_layout.addWidget(recent_table)
            else:
                no_transactions_label = QLabel("No recent transactions found")
                no_transactions_label.setStyleSheet("color: #999; font-style: italic; padding: 20px;")
                transactions_layout.addWidget(no_transactions_label)
                
        except Exception as e:
            print(f"[ERROR] Error creating recent transactions section: {e}")
            error_label = QLabel(f"Error loading recent transactions: {e}")
            error_label.setStyleSheet("color: red;")
            transactions_layout.addWidget(error_label)
        
        transactions_group.setLayout(transactions_layout)
        self.bank_dashboard_layout.addWidget(transactions_group)

    def create_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Bank Accounts section
        accounts_group = QGroupBox('Bank Account Management')
        accounts_layout = QVBoxLayout()
        
        manage_accounts_btn = QPushButton('Manage Bank Accounts')
        manage_accounts_btn.clicked.connect(self.manage_bank_accounts)
        manage_accounts_btn.setStyleSheet('QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px; }')
        accounts_layout.addWidget(manage_accounts_btn)
        
        accounts_info = QLabel('Add, edit, and manage your specific bank accounts (Tab Bank, Granite, Mountain America, etc.)')
        accounts_info.setWordWrap(True)
        accounts_info.setStyleSheet('color: #666; font-style: italic;')
        accounts_layout.addWidget(accounts_info)
        
        accounts_group.setLayout(accounts_layout)
        layout.addWidget(accounts_group)
        
        # Transaction Rules section
        rules_group = QGroupBox('Transaction Rules & Auto-Categorization')
        rules_layout = QVBoxLayout()
        
        manage_rules_btn = QPushButton('Manage Transaction Rules')
        manage_rules_btn.clicked.connect(self.manage_transaction_rules)
        manage_rules_btn.setStyleSheet('QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }')
        rules_layout.addWidget(manage_rules_btn)
        
        rules_info = QLabel('Create rules to automatically categorize transactions based on description patterns (e.g., "amazon" → "Shopping")')
        rules_info.setWordWrap(True)
        rules_info.setStyleSheet('color: #666; font-style: italic;')
        rules_layout.addWidget(rules_info)
        
        rules_group.setLayout(rules_layout)
        layout.addWidget(rules_group)
        
        # Tags section
        tags_group = QGroupBox('Tag Management')
        tags_layout = QVBoxLayout()
        
        manage_tags_btn = QPushButton('Manage Tags')
        manage_tags_btn.clicked.connect(self.manage_tags)
        manage_tags_btn.setStyleSheet('QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 10px; }')
        tags_layout.addWidget(manage_tags_btn)
        
        tags_info = QLabel('Create and manage tags for flexible transaction organization (e.g., "tax-deductible", "reimbursable", "work-related")')
        tags_info.setWordWrap(True)
        tags_info.setStyleSheet('color: #666; font-style: italic;')
        tags_layout.addWidget(tags_info)
        
        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)
        
        # Combined Finances section
        finances_group = QGroupBox('Combined Finances')
        finances_layout = QVBoxLayout()
        
        combine_btn = QPushButton('Combine Finances with Another User')
        combine_btn.clicked.connect(self.combine_finances)
        finances_layout.addWidget(combine_btn)
        
        # Show current combinations
        self.combined_label = QLabel('No combined finances')
        finances_layout.addWidget(self.combined_label)
        
        finances_group.setLayout(finances_layout)
        layout.addWidget(finances_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_loans_tab(self):
        """Create the Loans tab UI."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Controls
        controls = QHBoxLayout()
        add_btn = QPushButton('Add Loan')
        add_btn.clicked.connect(self.add_loan)
        controls.addWidget(add_btn)

        process_btn = QPushButton('Process Due Loans')
        process_btn.clicked.connect(self.process_loans)
        controls.addWidget(process_btn)

        controls.addStretch()
        layout.addLayout(controls)

        # Loans table
        self.loans_table = QTableWidget()
        self.loans_table.setColumnCount(11)
        self.loans_table.setHorizontalHeaderLabels([
            'Description', 'Loan Account', 'Pay From', 'Principal', 'Rate', 'Min Payment', 'Remaining', 'Frequency', 'Next Due', 'Status', 'Actions'
        ])
        header = self.loans_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Enable editing for specific columns only
        self.loans_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        # Connect signal for cell changes
        self.loans_table.cellChanged.connect(self.on_loan_cell_changed)
        layout.addWidget(self.loans_table)

        widget.setLayout(layout)
        return widget
    
    def create_budget_tab(self):
        """Create the Budgets tab UI"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        add_btn = QPushButton('Add Budget')
        add_btn.clicked.connect(self.add_budget)
        controls.addWidget(add_btn)
        
        refresh_btn = QPushButton('Refresh Budget Status')
        refresh_btn.clicked.connect(self.update_budget_table)
        controls.addWidget(refresh_btn)
        
        controls.addStretch()
        
        # Month selector for budget view
        controls.addWidget(QLabel('View Month:'))
        self.budget_month_selector = QDateEdit()
        self.budget_month_selector.setDate(QDate.currentDate())
        self.budget_month_selector.setCalendarPopup(True)
        self.budget_month_selector.setDisplayFormat('MMMM yyyy')
        self.budget_month_selector.dateChanged.connect(self.update_budget_table)
        controls.addWidget(self.budget_month_selector)
        
        layout.addLayout(controls)
        
        # Budget summary
        summary_group = QGroupBox("Budget Summary")
        summary_layout = QHBoxLayout()
        
        self.budget_summary_label = QLabel("Total Budgeted: $0.00 | Total Spent: $0.00 | Remaining: $0.00")
        self.budget_summary_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        summary_layout.addWidget(self.budget_summary_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Budgets table
        self.budgets_table = QTableWidget()
        self.budgets_table.setColumnCount(7)
        self.budgets_table.setHorizontalHeaderLabels([
            'Category', 'Monthly Limit', 'Spent', 'Remaining', 'Progress %', 'Status', 'Actions'
        ])
        header = self.budgets_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.budgets_table)
        
        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Legend:"))
        
        good_label = QLabel("● Good (Under Budget)")
        good_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        legend_layout.addWidget(good_label)
        
        warning_label = QLabel("● Warning (Approaching Limit)")
        warning_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        legend_layout.addWidget(warning_label)
        
        over_label = QLabel("● Over Budget")
        over_label.setStyleSheet("color: #F44336; font-weight: bold;")
        legend_layout.addWidget(over_label)
        
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
        widget.setLayout(layout)
        return widget
    
    def set_current_user(self, user_id):
        """Set the current user and refresh data"""
        self.current_user_id = user_id
        self.bank.set_current_user(user_id)
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh all data displays"""
        print("[DEBUG] refresh_data: Starting data refresh...")
        try:
            print("[DEBUG] refresh_data: Updating overview...")
            self.update_overview()
            print("[DEBUG] refresh_data: Overview updated")
            
            print("[DEBUG] refresh_data: Updating transactions table...")
            self.update_transactions_table()
            print("[DEBUG] refresh_data: Transactions table updated")
            
            print("[DEBUG] refresh_data: Updating recurring table...")
            self.update_recurring_table()
            print("[DEBUG] refresh_data: Recurring table updated")

            # Loans table
            print("[DEBUG] refresh_data: Updating loans table...")
            self.update_loans_table()
            print("[DEBUG] refresh_data: Loans table updated")
            
            # Budget table
            print("[DEBUG] refresh_data: Updating budget table...")
            self.update_budget_table()
            print("[DEBUG] refresh_data: Budget table updated")
            
            # Goals display
            print("[DEBUG] refresh_data: Updating goals display...")
            self.update_goals_display()
            print("[DEBUG] refresh_data: Goals display updated")
            
            # Net Worth display
            print("[DEBUG] refresh_data: Updating net worth display...")
            self.update_net_worth_display()
            print("[DEBUG] refresh_data: Net worth display updated")
            
            # Refresh delegates with updated data
            print("[DEBUG] refresh_data: Setting up table delegates...")
            try:
                self.setup_table_delegates()
                print("[DEBUG] refresh_data: Delegates refreshed successfully")
            except Exception as e:
                print(f"[ERROR] refresh_data: Error setting up delegates: {e}")
                import traceback
                traceback.print_exc()
            print("[DEBUG] refresh_data: Table delegates set up")
            
            print("[DEBUG] refresh_data: Updating settings display...")
            self.update_settings_display()
            print("[DEBUG] refresh_data: Settings display updated")
            
            print("[DEBUG] refresh_data: Data refresh completed successfully")
            
        except Exception as e:
            print(f"[ERROR] refresh_data: Error refreshing data: {e}")
            import traceback
            traceback.print_exc()
    
    def update_overview(self):
        """Update the overview tab with current financial summary"""
        summary = self.bank.get_financial_summary(self.current_user_id)
        
        self.income_label.setText(f'Total Income: ${summary["total_income"]:.2f}')
        self.expense_label.setText(f'Total Expenses: ${summary["total_expenses"]:.2f}')
        self.balance_label.setText(f'Net Balance: ${summary["net_balance"]:.2f}')
        
        # Update balance color
        if summary["net_balance"] >= 0:
            self.balance_label.setStyleSheet('font-size: 14px; font-weight: bold; color: green;')
        else:
            self.balance_label.setStyleSheet('font-size: 14px; font-weight: bold; color: red;')
        
        self.update_charts(summary)
        self.update_upcoming_payments()
        self.update_overdue_payments()
    
    def update_upcoming_payments(self):
        """Update the upcoming payments table"""
        try:
            recurring_transactions = self.bank.get_recurring_transactions(self.current_user_id)
            upcoming = []
            
            # Filter for upcoming payments in next 30 days
            for recurring in recurring_transactions:
                try:
                    next_due = recurring.get_next_due_date()
                    if next_due and next_due <= date.today() + timedelta(days=30):
                        upcoming.append({
                            'description': recurring.desc,
                            'amount': recurring.amount,
                            'due_date': next_due,
                            'category': recurring.category,
                            'type': getattr(recurring, 'type_', recurring.type)  # Safe access to type_
                        })
                except Exception as e:
                    print(f"[WARNING] Error processing recurring transaction: {e}")
                    continue
            
            # Sort by due date
            upcoming.sort(key=lambda x: x['due_date'])
            
            self.upcoming_table.setRowCount(len(upcoming))
            for row, payment in enumerate(upcoming):
                self.upcoming_table.setItem(row, 0, QTableWidgetItem(payment['description']))
                amount_str = f"${payment['amount']:,.2f}"
                if payment['type'] == 'out':
                    amount_str = f"-{amount_str}"
                self.upcoming_table.setItem(row, 1, QTableWidgetItem(amount_str))
                self.upcoming_table.setItem(row, 2, QTableWidgetItem(payment['due_date'].strftime('%Y-%m-%d')))
                self.upcoming_table.setItem(row, 3, QTableWidgetItem(payment['category']))
                
        except Exception as e:
            print(f"Error updating upcoming payments: {e}")
    
    def update_overdue_payments(self):
        """Update the overdue payments table"""
        try:
            recurring_transactions = self.bank.get_recurring_transactions(self.current_user_id)
            overdue = []
            
            # Find overdue recurring transactions
            for recurring in recurring_transactions:
                try:
                    next_due = recurring.get_next_due_date()
                    if next_due and next_due < date.today():
                        days_late = (date.today() - next_due).days
                        overdue.append({
                            'description': recurring.desc,
                            'amount': recurring.amount,
                            'due_date': next_due,
                            'days_late': days_late,
                            'category': recurring.category,
                            'type': getattr(recurring, 'type_', recurring.type)  # Safe access to type_
                        })
                except Exception as e:
                    print(f"[WARNING] Error processing overdue recurring transaction: {e}")
                    continue
            
            # Sort by days late (most late first)
            overdue.sort(key=lambda x: x['days_late'], reverse=True)
            
            self.overdue_table.setRowCount(len(overdue))
            for row, payment in enumerate(overdue):
                self.overdue_table.setItem(row, 0, QTableWidgetItem(payment['description']))
                amount_str = f"${payment['amount']:,.2f}"
                if payment['type'] == 'out':
                    amount_str = f"-{amount_str}"
                self.overdue_table.setItem(row, 1, QTableWidgetItem(amount_str))
                self.overdue_table.setItem(row, 2, QTableWidgetItem(payment['due_date'].strftime('%Y-%m-%d')))
                self.overdue_table.setItem(row, 3, QTableWidgetItem(f"{payment['days_late']} days"))
                self.overdue_table.setItem(row, 4, QTableWidgetItem(payment['category']))
                
        except Exception as e:
            print(f"Error updating overdue payments: {e}")
    
    def update_charts(self, summary):
        """Update the overview charts"""
        try:
            # Income vs Expenses chart
            self.overview_chart.figure.clear()
            ax1 = self.overview_chart.figure.add_subplot(111)
            
            if summary['total_income'] > 0 or summary['total_expenses'] > 0:
                data = [summary['total_income'], summary['total_expenses']]
                labels = ['Income', 'Expenses']
                colors = ['#4CAF50', '#F44336']
                ax1.pie(data, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
                ax1.set_title('Income vs Expenses')
            else:
                ax1.text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=14)
                ax1.set_title('Income vs Expenses')
            
            self.overview_chart.figure.tight_layout()
            self.overview_chart.draw()
            
            # Category breakdown chart
            self.category_chart.figure.clear()
            ax2 = self.category_chart.figure.add_subplot(111)
            
            expense_categories = summary['expense_by_category']
            if expense_categories:
                categories = list(expense_categories.keys())
                amounts = list(expense_categories.values())
                ax2.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
                ax2.set_title('Expenses by Category')
            else:
                ax2.text(0.5, 0.5, 'No Expense Data', ha='center', va='center', fontsize=14)
                ax2.set_title('Expenses by Category')
            
            self.category_chart.figure.tight_layout()
            self.category_chart.draw()
            
        except Exception as e:
            print(f"Error updating charts: {e}")
    
    def update_transactions_table(self):
        """Update the transactions table"""
        try:
            # Block signals during population to avoid triggering handlers mid-update
            try:
                self.transactions_table.blockSignals(True)
            except Exception as e:
                print(f"[WARNING] Could not block signals: {e}")

            transactions = self.bank.list_transactions(user_id=self.current_user_id)
            
            transactions.sort(key=lambda x: x['timestamp'], reverse=True)  # Most recent first
            
            self.transactions_table.setRowCount(len(transactions))
            
            # Clear and repopulate original transactions store
            self.original_transactions = {}
            
            # Ensure the correct signal is disconnected to avoid duplicate connections
            try:
                self.transactions_table.cellChanged.disconnect(self.on_transaction_cell_changed)
            except TypeError:
                # Signal was not connected, continue
                pass
            except Exception as e:
                print(f"[ERROR] Error disconnecting cellChanged: {e}")
            
            for row, tx in enumerate(transactions):
                # Store original transaction data
                self.original_transactions[row] = tx.copy()
                
                # Check budget status for this transaction
                budget_status = self.budget_manager.check_transaction(tx, transactions)
                
                # Date (now editable with date picker)
                tx_date = datetime.fromisoformat(tx['timestamp']).strftime('%Y-%m-%d')
                date_item = QTableWidgetItem(tx_date)
                # Apply budget color if available
                if budget_status['color']:
                    date_item.setBackground(QBrush(QColor(budget_status['color'])))
                self.transactions_table.setItem(row, 0, date_item)
                
                # Description (editable)
                desc_item = QTableWidgetItem(tx['desc'])
                if budget_status['color']:
                    desc_item.setBackground(QBrush(QColor(budget_status['color'])))
                self.transactions_table.setItem(row, 1, desc_item)
                
                # Category (editable) - show split indicator if transaction is split
                splits = tx.get('splits', [])
                if splits:
                    # Transaction is split - show "Split" with icon
                    split_categories = [s['category'] for s in splits]
                    category_text = f"🔀 Split ({len(splits)}): {', '.join(split_categories)}"
                    category_item = QTableWidgetItem(category_text)
                    category_item.setToolTip('\n'.join([f"{s['category']}: ${s['amount']:.2f}" for s in splits]))
                else:
                    category_item = QTableWidgetItem(tx.get('category', 'N/A'))
                
                if budget_status['color']:
                    category_item.setBackground(QBrush(QColor(budget_status['color'])))
                self.transactions_table.setItem(row, 2, category_item)
                
                # Account (now editable - will show available accounts)
                account_item = QTableWidgetItem(tx['account'])
                if budget_status['color']:
                    account_item.setBackground(QBrush(QColor(budget_status['color'])))
                self.transactions_table.setItem(row, 3, account_item)
                
                # Type (now editable - Income/Expense/Loan Payment)
                if tx['type'] == 'in':
                    type_text = 'Income'
                elif tx['type'] == 'loan_payment':
                    type_text = 'Loan Payment'
                else:
                    type_text = 'Expense'
                type_item = QTableWidgetItem(type_text)
                if tx['type'] == 'in':
                    type_item.setForeground(QBrush(QColor('green')))
                elif tx['type'] == 'loan_payment':
                    type_item.setForeground(QBrush(QColor('blue')))  # Blue for loan payments
                else:
                    type_item.setForeground(QBrush(QColor('red')))
                if budget_status['color']:
                    type_item.setBackground(QBrush(QColor(budget_status['color'])))
                self.transactions_table.setItem(row, 4, type_item)
                
                # Amount (editable)
                amount_item = QTableWidgetItem(f'{tx["amount"]:.2f}')  # Remove $ for easier editing
                if tx['type'] == 'in':
                    amount_item.setForeground(QBrush(QColor('green')))
                else:
                    amount_item.setForeground(QBrush(QColor('red')))
                if budget_status['color']:
                    amount_item.setBackground(QBrush(QColor(budget_status['color'])))
                self.transactions_table.setItem(row, 5, amount_item)
                
                # Attachments indicator
                attachments = tx.get('attachments', [])
                if attachments and len(attachments) > 0:
                    attachment_btn = QPushButton(f'📎 {len(attachments)}')
                    attachment_btn.setToolTip(f'{len(attachments)} attachment(s)')
                    attachment_btn.setMaximumWidth(50)
                    attachment_btn.clicked.connect(lambda checked, transaction=tx: self.view_transaction_attachments(transaction))
                    if budget_status['color']:
                        attachment_btn.setStyleSheet(f"background-color: {budget_status['color']};")
                    self.transactions_table.setCellWidget(row, 6, attachment_btn)
                else:
                    empty_item = QTableWidgetItem('')
                    if budget_status['color']:
                        empty_item.setBackground(QBrush(QColor(budget_status['color'])))
                    self.transactions_table.setItem(row, 6, empty_item)
                
                # Actions (Delete button)
                delete_btn = QPushButton('Delete')
                delete_btn.clicked.connect(lambda checked, t=tx: self.delete_transaction(t))
                self.transactions_table.setCellWidget(row, 7, delete_btn)
            
            try:
                self.transactions_table.cellChanged.connect(self.on_transaction_cell_changed)
            except AttributeError:
                pass
            except Exception as e:
                print(f"[ERROR] Error connecting cellChanged: {e}")
            
            # Populate filter options after updating table
            self.populate_filter_options()
            
        except Exception as e:
            print(f"[ERROR] Error updating transactions table: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always unblock signals after population
            try:
                self.transactions_table.blockSignals(False)
            except Exception as e:
                print(f"[WARNING] Could not unblock signals: {e}")
    
    def update_recurring_table(self):
        """Update the recurring transactions table"""
        print("[DEBUG] update_recurring_table: Starting recurring table update...")
        try:
            # Block signals during table population to prevent triggering cellChanged
            self.recurring_table.blockSignals(True)
            print("[DEBUG] update_recurring_table: Signals blocked")
            
            recurring_txs = self.bank.list_recurring_transactions(self.current_user_id)
            self.recurring_table.setRowCount(len(recurring_txs))
            print(f"[DEBUG] update_recurring_table: Processing {len(recurring_txs)} recurring transactions")
            
            for row, rtx in enumerate(recurring_txs):
                # Description
                self.recurring_table.setItem(row, 0, QTableWidgetItem(rtx['desc']))
                
                # Category
                self.recurring_table.setItem(row, 1, QTableWidgetItem(rtx.get('category', 'N/A')))
                
                # Account
                self.recurring_table.setItem(row, 2, QTableWidgetItem(rtx['account']))
                
                # Type - Handle both dictionary and object access
                tx_type = rtx.get('type', rtx.get('type_', 'out'))  # Default to 'out' if not found
                if tx_type == 'in':
                    type_text = 'Income'
                elif tx_type == 'loan_payment':
                    type_text = 'Loan Payment'
                else:
                    type_text = 'Expense'
                self.recurring_table.setItem(row, 3, QTableWidgetItem(type_text))
                
                # Amount - Show range for variable amounts
                amount_type = rtx.get('amount_type', 'fixed')
                if amount_type == 'variable' and rtx.get('amount_min') and rtx.get('amount_max'):
                    amount_text = f'${rtx["amount_min"]:.2f} - ${rtx["amount_max"]:.2f}'
                elif amount_type == 'prompt':
                    amount_text = 'Prompt'
                else:
                    amount_text = f'${rtx["amount"]:.2f}'
                self.recurring_table.setItem(row, 4, QTableWidgetItem(amount_text))
                
                # Frequency
                self.recurring_table.setItem(row, 5, QTableWidgetItem(rtx['frequency'].title()))
                
                # Status
                status = rtx.get('status', 'active')
                status_item = QTableWidgetItem(status.title())
                if status == 'paused':
                    status_item.setForeground(QBrush(QColor('#FFA500')))  # Orange for paused
                elif status == 'completed':
                    status_item.setForeground(QBrush(QColor('#808080')))  # Gray for completed
                else:
                    status_item.setForeground(QBrush(QColor('#4CAF50')))  # Green for active
                self.recurring_table.setItem(row, 6, status_item)
                
                # Next Due
                from src.bank import RecurringTransaction
                recurring_obj = RecurringTransaction.from_dict(rtx)
                
                if rtx.get('skip_next'):
                    next_due_text = 'Skipped'
                elif status == 'paused':
                    next_due_text = 'Paused'
                else:
                    next_due = recurring_obj.get_next_due_date()
                    next_due_text = next_due.strftime('%Y-%m-%d')
                self.recurring_table.setItem(row, 7, QTableWidgetItem(next_due_text))
                
                # Instances created count
                instances = rtx.get('instances_created', [])
                instances_item = QTableWidgetItem(str(len(instances)))
                self.recurring_table.setItem(row, 8, instances_item)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(2, 2, 2, 2)
                actions_layout.setSpacing(4)
                
                # Pause/Resume button
                if status == 'paused':
                    pause_resume_btn = QPushButton('Resume')
                    pause_resume_btn.clicked.connect(lambda checked, rt=rtx: self.resume_recurring_transaction(rt))
                else:
                    pause_resume_btn = QPushButton('Pause')
                    pause_resume_btn.clicked.connect(lambda checked, rt=rtx: self.pause_recurring_transaction(rt))
                pause_resume_btn.setMaximumWidth(70)
                actions_layout.addWidget(pause_resume_btn)
                
                # Skip Next button
                skip_btn = QPushButton('Skip')
                skip_btn.clicked.connect(lambda checked, rt=rtx: self.skip_next_recurring(rt))
                skip_btn.setMaximumWidth(60)
                skip_btn.setEnabled(status == 'active')
                actions_layout.addWidget(skip_btn)
                
                # Process Now button
                process_btn = QPushButton('Now')
                process_btn.clicked.connect(lambda checked, rt=rtx: self.process_recurring_now(rt))
                process_btn.setMaximumWidth(50)
                actions_layout.addWidget(process_btn)
                
                # History button
                history_btn = QPushButton('History')
                history_btn.clicked.connect(lambda checked, rt=rtx: self.show_recurring_history(rt))
                history_btn.setMaximumWidth(70)
                actions_layout.addWidget(history_btn)
                
                # Delete button
                delete_btn = QPushButton('Delete')
                delete_btn.clicked.connect(lambda checked, rt=rtx: self.delete_recurring_transaction(rt))
                delete_btn.setMaximumWidth(70)
                actions_layout.addWidget(delete_btn)
                
                actions_widget.setLayout(actions_layout)
                self.recurring_table.setCellWidget(row, 9, actions_widget)
        except Exception as e:
            print(f"[ERROR] update_recurring_table: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always unblock signals
            self.recurring_table.blockSignals(False)
            print("[DEBUG] update_recurring_table: Signals unblocked")
    
    def update_settings_display(self):
        """Update the settings display"""
        combined_users = self.bank.get_combined_users(self.current_user_id)
        if combined_users:
            self.combined_label.setText(f'Combined with: {", ".join(combined_users)}')
        else:
            self.combined_label.setText('No combined finances')
    
    def add_transaction(self):
        """Add a new transaction"""
        dialog = AddTransactionDialog(self, self.bank, is_recurring=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            # Create transaction
            transaction = self.bank.add_transaction(
                amount=data['amount'],
                desc=data['desc'],
                account=data['account'],
                account_id=data.get('account_id'),
                type_=data['type'],
                category=data['category'],
                user_id=self.current_user_id,
                splits=data.get('splits'),
                attachments=data.get('attachments')
            )
            
            # Auto-apply transaction rules if category is not already set or is 'Uncategorized'
            if transaction and hasattr(self, 'rule_manager'):
                tx_category = transaction.get('category', '')
                if not tx_category or tx_category == 'Uncategorized':
                    matched = self.rule_manager.apply_rules(transaction)
                    if matched:
                        # Transaction was auto-categorized, save the changes
                        self.bank.save_data()
            
            self.refresh_data()
    
    def add_recurring_transaction(self):
        """Add a new recurring transaction"""
        dialog = AddTransactionDialog(self, self.bank, is_recurring=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.bank.add_recurring_transaction(
                amount=data['amount'],
                desc=data['desc'],
                account=data['account'],
                account_id=data.get('account_id'),
                type_=data['type'],
                category=data['category'],
                frequency=data['frequency'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                user_id=self.current_user_id
            )
            self.refresh_data()
    
    def process_recurring(self):
        """Process all due recurring transactions"""
        count = self.bank.process_recurring_transactions()
        QMessageBox.information(self, 'Recurring Transactions', 
                              f'Processed {count} recurring transactions.')
        self.refresh_data()
    
    def combine_finances(self):
        """Combine finances with another user"""
        dialog = CombineFinancesDialog(self, self.current_user_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            other_user = dialog.get_selected_user()
            self.bank.combine_user_finances(self.current_user_id, other_user)
            QMessageBox.information(self, 'Success', 
                                  f'Finances combined with {other_user}')
            self.refresh_data()
    
    def manage_bank_accounts(self):
        """Open bank account management dialog"""
        from ui.bank_account_management_dialog import BankAccountManagementDialog
        dialog = BankAccountManagementDialog(self, self.bank, self.current_user_id)
        dialog.accounts_changed.connect(self.refresh_data)  # Refresh when accounts change
        dialog.exec()
    
    def manage_transaction_rules(self):
        """Open transaction rules management dialog"""
        dialog = RuleManagerDialog(self, self.rule_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Rules may have been modified, refresh data in case apply-all was used
            self.refresh_data()
    
    def manage_tags(self):
        """Open tag management dialog"""
        dialog = TagManagerDialog(self, self.tag_manager, self.bank.list_transactions(user_id=self.current_user_id))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Tags may have been modified, refresh data
            self.refresh_data()
    
    def setup_table_delegates(self):
        """Set up custom delegates for dropdown editing in the transactions table"""
        print("[DEBUG] setup_table_delegates: Starting delegate setup...")
        try:
            # Column 0: Date - Date picker for editing
            print("[DEBUG] setup_table_delegates: Setting up date delegate...")
            # Keep a strong reference and parent to the table to avoid GC-related crashes
            self.date_delegate = SimpleDateDelegate(parent=self.transactions_table)
            self.transactions_table.setItemDelegateForColumn(0, self.date_delegate)
            print("[DEBUG] setup_table_delegates: Date delegate set successfully")

            # Column 1: Description - Default text editing (no custom delegate needed)
            print("[DEBUG] setup_table_delegates: Description column - no delegate needed")

            # Column 2: Category - Dropdown with common categories
            print("[DEBUG] setup_table_delegates: Setting up category delegate...")
            categories = self.get_common_categories()
            print(f"[DEBUG] setup_table_delegates: Loaded {len(categories)} categories")
            if categories:  # Only set delegate if we have categories
                self.category_delegate = SimpleComboDelegate(categories, parent=self.transactions_table)
                self.transactions_table.setItemDelegateForColumn(2, self.category_delegate)
                print("[DEBUG] setup_table_delegates: Category delegate set successfully")
            else:
                print("[WARNING] setup_table_delegates: No categories available, skipping category delegate")

            # Column 3: Account - Dropdown with available accounts
            print("[DEBUG] setup_table_delegates: Setting up account delegate...")
            accounts = self.get_available_accounts()
            print(f"[DEBUG] setup_table_delegates: Loaded {len(accounts)} accounts")
            if accounts:  # Only set delegate if we have accounts
                self.account_delegate = SimpleComboDelegate(accounts, parent=self.transactions_table)
                self.transactions_table.setItemDelegateForColumn(3, self.account_delegate)
                print("[DEBUG] setup_table_delegates: Account delegate set successfully")
            else:
                print("[WARNING] setup_table_delegates: No accounts available, skipping account delegate")

            # Column 4: Type - Dropdown with Income/Expense
            print("[DEBUG] setup_table_delegates: Setting up type delegate...")
            type_items = ['Income', 'Expense']
            self.type_delegate = SimpleComboDelegate(type_items, parent=self.transactions_table)
            self.transactions_table.setItemDelegateForColumn(4, self.type_delegate)
            print("[DEBUG] setup_table_delegates: Type delegate set successfully")

            # Column 5: Amount - Numeric spinner with currency formatting
            print("[DEBUG] setup_table_delegates: Setting up amount delegate...")
            self.amount_delegate = SimpleAmountDelegate(parent=self.transactions_table)
            self.transactions_table.setItemDelegateForColumn(5, self.amount_delegate)
            print("[DEBUG] setup_table_delegates: Amount delegate set successfully")

            # Column 6: Actions - No editing (buttons)
            print("[DEBUG] setup_table_delegates: Actions column - no delegate needed")

            print("[DEBUG] setup_table_delegates: All delegates setup completed successfully")

        except Exception as e:
            print(f"[ERROR] setup_table_delegates: Error setting up table delegates: {e}")
            import traceback
            traceback.print_exc()
            # Continue without delegates if there's an error
    
    def setup_recurring_table_delegates(self):
        """Set up custom delegates for dropdown editing in the recurring transactions table"""
        print("[DEBUG] setup_recurring_table_delegates: Starting delegate setup...")
        try:
            # Column 0: Description - Default text editing (no custom delegate needed)
            print("[DEBUG] setup_recurring_table_delegates: Description column - no delegate needed")

            # Column 1: Category - Dropdown with common categories
            print("[DEBUG] setup_recurring_table_delegates: Setting up category delegate...")
            categories = self.get_common_categories()
            print(f"[DEBUG] setup_recurring_table_delegates: Loaded {len(categories)} categories")
            if categories:
                self.recurring_category_delegate = SimpleComboDelegate(categories, parent=self.recurring_table)
                self.recurring_table.setItemDelegateForColumn(1, self.recurring_category_delegate)
                print("[DEBUG] setup_recurring_table_delegates: Category delegate set successfully")

            # Column 2: Account - Dropdown with available accounts  
            print("[DEBUG] setup_recurring_table_delegates: Setting up account delegate...")
            accounts = self.get_available_accounts()
            print(f"[DEBUG] setup_recurring_table_delegates: Loaded {len(accounts)} accounts")
            if accounts:
                self.recurring_account_delegate = SimpleComboDelegate(accounts, parent=self.recurring_table)
                self.recurring_table.setItemDelegateForColumn(2, self.recurring_account_delegate)
                print("[DEBUG] setup_recurring_table_delegates: Account delegate set successfully")

            # Column 3: Type - Dropdown with Income/Expense/Loan Payment
            print("[DEBUG] setup_recurring_table_delegates: Setting up type delegate...")
            type_items = ['Income', 'Expense', 'Loan Payment']
            self.recurring_type_delegate = SimpleComboDelegate(type_items, parent=self.recurring_table)
            self.recurring_table.setItemDelegateForColumn(3, self.recurring_type_delegate)
            print("[DEBUG] setup_recurring_table_delegates: Type delegate set successfully")

            # Column 4: Amount - Numeric spinner with currency formatting
            print("[DEBUG] setup_recurring_table_delegates: Setting up amount delegate...")
            self.recurring_amount_delegate = SimpleAmountDelegate(parent=self.recurring_table)
            self.recurring_table.setItemDelegateForColumn(4, self.recurring_amount_delegate)
            print("[DEBUG] setup_recurring_table_delegates: Amount delegate set successfully")

            # Column 5: Frequency - Dropdown with frequency options
            print("[DEBUG] setup_recurring_table_delegates: Setting up frequency delegate...")
            frequency_items = ['Weekly', 'Monthly', 'Yearly']
            self.recurring_frequency_delegate = SimpleComboDelegate(frequency_items, parent=self.recurring_table)
            self.recurring_table.setItemDelegateForColumn(5, self.recurring_frequency_delegate)
            print("[DEBUG] setup_recurring_table_delegates: Frequency delegate set successfully")

            # Column 6: Next Due - Date picker for editing
            print("[DEBUG] setup_recurring_table_delegates: Setting up next due date delegate...")
            self.recurring_date_delegate = SimpleDateDelegate(parent=self.recurring_table)
            self.recurring_table.setItemDelegateForColumn(6, self.recurring_date_delegate)
            print("[DEBUG] setup_recurring_table_delegates: Next due date delegate set successfully")

            # Column 7: Actions - No editing (buttons)
            print("[DEBUG] setup_recurring_table_delegates: Actions column - no delegate needed")

            print("[DEBUG] setup_recurring_table_delegates: All delegates setup completed successfully")

        except Exception as e:
            print(f"[ERROR] setup_recurring_table_delegates: Error setting up recurring table delegates: {e}")
            import traceback
            traceback.print_exc()
            # Continue without delegates if there's an error
    
    def setup_loans_table_delegates(self):
        """Set up custom delegates for dropdown editing in the loans table"""
        print("[DEBUG] setup_loans_table_delegates: Starting delegate setup...")
        try:
            # Column 0: Description - Default text editing (no custom delegate needed)
            print("[DEBUG] setup_loans_table_delegates: Description column - no delegate needed")

            # Column 1: Loan Account - Dropdown with available accounts
            print("[DEBUG] setup_loans_table_delegates: Setting up loan account delegate...")
            accounts = self.get_available_accounts()
            print(f"[DEBUG] setup_loans_table_delegates: Loaded {len(accounts)} accounts")
            if accounts:
                self.loans_account_delegate = SimpleComboDelegate(accounts, parent=self.loans_table)
                self.loans_table.setItemDelegateForColumn(1, self.loans_account_delegate)
                print("[DEBUG] setup_loans_table_delegates: Loan account delegate set successfully")

            # Column 2: Pay From Account - Dropdown with available non-loan accounts
            print("[DEBUG] setup_loans_table_delegates: Setting up pay from account delegate...")
            if accounts:
                # Filter out loan accounts for pay from selection
                non_loan_accounts = [acc for acc in accounts if 'loan' not in acc.lower()]
                self.loans_pay_from_delegate = SimpleComboDelegate(non_loan_accounts, parent=self.loans_table)
                self.loans_table.setItemDelegateForColumn(2, self.loans_pay_from_delegate)
                print("[DEBUG] setup_loans_table_delegates: Pay from account delegate set successfully")

            # Column 3: Principal - Numeric spinner with currency formatting
            print("[DEBUG] setup_loans_table_delegates: Setting up principal delegate...")
            self.loans_principal_delegate = SimpleAmountDelegate(parent=self.loans_table)
            self.loans_table.setItemDelegateForColumn(3, self.loans_principal_delegate)
            print("[DEBUG] setup_loans_table_delegates: Principal delegate set successfully")

            # Column 4: Rate - Percentage input
            print("[DEBUG] setup_loans_table_delegates: Setting up rate delegate...")
            # Use amount delegate but will be handled specially in validation
            self.loans_rate_delegate = SimpleAmountDelegate(parent=self.loans_table)
            self.loans_table.setItemDelegateForColumn(4, self.loans_rate_delegate)
            print("[DEBUG] setup_loans_table_delegates: Rate delegate set successfully")

            # Column 5: Payment - Numeric spinner with currency formatting
            print("[DEBUG] setup_loans_table_delegates: Setting up payment delegate...")
            self.loans_payment_delegate = SimpleAmountDelegate(parent=self.loans_table)
            self.loans_table.setItemDelegateForColumn(5, self.loans_payment_delegate)
            print("[DEBUG] setup_loans_table_delegates: Payment delegate set successfully")

            # Column 6: Remaining - Read-only (calculated field)
            print("[DEBUG] setup_loans_table_delegates: Remaining column - read-only")

            # Column 7: Frequency - Dropdown with frequency options
            print("[DEBUG] setup_loans_table_delegates: Setting up frequency delegate...")
            frequency_items = ['Weekly', 'Monthly', 'Yearly']
            self.loans_frequency_delegate = SimpleComboDelegate(frequency_items, parent=self.loans_table)
            self.loans_table.setItemDelegateForColumn(7, self.loans_frequency_delegate)
            print("[DEBUG] setup_loans_table_delegates: Frequency delegate set successfully")

            # Column 8: Next Due - Date picker for editing
            print("[DEBUG] setup_loans_table_delegates: Setting up next due date delegate...")
            self.loans_date_delegate = SimpleDateDelegate(parent=self.loans_table)
            self.loans_table.setItemDelegateForColumn(8, self.loans_date_delegate)
            print("[DEBUG] setup_loans_table_delegates: Next due date delegate set successfully")

            # Column 9: Status - Dropdown with status options
            print("[DEBUG] setup_loans_table_delegates: Setting up status delegate...")
            status_items = ['Active', 'Completed', 'Inactive']
            self.loans_status_delegate = SimpleComboDelegate(status_items, parent=self.loans_table)
            self.loans_table.setItemDelegateForColumn(9, self.loans_status_delegate)
            print("[DEBUG] setup_loans_table_delegates: Status delegate set successfully")

            # Column 10: Actions - No editing (buttons)
            print("[DEBUG] setup_loans_table_delegates: Actions column - no delegate needed")

            print("[DEBUG] setup_loans_table_delegates: All delegates setup completed successfully")

        except Exception as e:
            print(f"[ERROR] setup_loans_table_delegates: Error setting up loans table delegates: {e}")
            import traceback
            traceback.print_exc()
            # Continue without delegates if there's an error
    
    def get_common_categories(self):
        """Get list of common transaction categories"""
        print("[DEBUG] get_common_categories: Starting category loading...")
        try:
            print("[DEBUG] get_common_categories: Getting existing categories from transactions...")
            # Get existing categories from transactions
            transactions = self.bank.list_transactions(user_id=self.current_user_id)
            existing_categories = set(tx.get('category') for tx in transactions if tx.get('category'))
            print(f"[DEBUG] get_common_categories: Found {len(existing_categories)} existing categories")
        except Exception as e:
            print(f"[ERROR] get_common_categories: Error getting existing categories: {e}")
            import traceback
            traceback.print_exc()
            existing_categories = set()
        
        # Common financial categories
        common_categories = [
            'Food & Dining', 'Shopping', 'Entertainment', 'Bills & Utilities',
            'Transportation', 'Health & Medical', 'Travel', 'Education',
            'Gifts & Donations', 'Investment', 'Business', 'Personal Care',
            'Home & Garden', 'Automotive', 'Insurance', 'Taxes',
            'Income', 'Salary', 'Freelance', 'Investment Income', 'Other'
        ]
        print(f"[DEBUG] get_common_categories: Using {len(common_categories)} common categories")
        
        # Combine and return unique categories
        all_categories = list(existing_categories.union(set(common_categories)))
        result = sorted([cat for cat in all_categories if cat and cat != 'N/A'])
        print(f"[DEBUG] get_common_categories: Returning {len(result)} total categories")
        return result
    
    def get_available_accounts(self):
        """Get list of available account names for validation"""
        print("[DEBUG] get_available_accounts: Starting account loading...")
        try:
            print("[DEBUG] get_available_accounts: Getting bank accounts...")
            # Get bank accounts (enhanced accounts)
            bank_accounts = self.bank.get_user_bank_accounts(self.current_user_id)
            account_names = [acc.get_display_name() for acc in bank_accounts]
            print(f"[DEBUG] get_available_accounts: Found {len(account_names)} bank accounts")
        except Exception as e:
            print(f"[ERROR] get_available_accounts: Error getting bank accounts: {e}")
            import traceback
            traceback.print_exc()
            account_names = []
        
        try:
            print("[DEBUG] get_available_accounts: Getting existing accounts from transactions...")
            # Also include existing account names from transactions for backward compatibility
            transactions = self.bank.list_transactions(user_id=self.current_user_id)
            existing_accounts = set(tx['account'] for tx in transactions if tx.get('account'))
            print(f"[DEBUG] get_available_accounts: Found {len(existing_accounts)} existing accounts from transactions")
        except Exception as e:
            print(f"[ERROR] get_available_accounts: Error getting existing accounts from transactions: {e}")
            import traceback
            traceback.print_exc()
            existing_accounts = set()
        
        # Combine and return unique accounts
        all_accounts = list(set(account_names + list(existing_accounts)))
        print(f"[DEBUG] get_available_accounts: Combined accounts: {len(all_accounts)}")
        
        # Provide fallback accounts if none found
        if not all_accounts:
            all_accounts = ['Main Account', 'Checking', 'Savings']
            print(f"[DEBUG] get_available_accounts: Using fallback accounts: {all_accounts}")
        
        result = sorted(all_accounts)
        print(f"[DEBUG] get_available_accounts: Returning {len(result)} accounts: {result}")
        return result
    
    def validate_account_name(self, account_name):
        """Validate if account name is acceptable"""
        if not account_name.strip():
            return False, "Account name cannot be empty"
        
        # Allow any non-empty account name (user might be creating new account)
        return True, ""
    
    def validate_transaction_type(self, type_text):
        """Validate transaction type"""
        valid_types = ['Income', 'Expense', 'Loan Payment']
        if type_text not in valid_types:
            return False, f"Type must be one of: {', '.join(valid_types)}"
        return True, ""
    
    def on_transaction_cell_changed(self, row, column):
        """Handle when a transaction cell is edited"""
        print(f"[DEBUG] on_transaction_cell_changed: SIGNAL TRIGGERED - Cell changed - Row: {row}, Column: {column}")

        # Prevent recursive signal calls
        if self._signal_processing:
            print("[DEBUG] on_transaction_cell_changed: Recursive call detected, ignoring")
            return

        self._signal_processing = True
        try:
            print(f"[DEBUG] on_transaction_cell_changed: Processing change for row {row}, column {column}")

            # Handle all editable columns: Date (0), Description (1), Category (2), Account (3), Type (4), Amount (5)
            if column not in [0, 1, 2, 3, 4, 5]:
                print(f"[DEBUG] on_transaction_cell_changed: Column {column} is not editable, ignoring")
                return
            
            # Get original transaction
            print(f"[DEBUG] on_transaction_cell_changed: Getting original transaction for row {row}")
            if row not in self.original_transactions:
                print(f"[ERROR] on_transaction_cell_changed: No original transaction found for row {row}")
                return
            
            original_tx = self.original_transactions[row]
            print(f"[DEBUG] on_transaction_cell_changed: Original transaction retrieved: {original_tx.get('desc', 'N/A')}")
            
            # Get current values from the table with null checks
            print(f"[DEBUG] on_transaction_cell_changed: Getting current values from table...")
            date_item = self.transactions_table.item(row, 0)
            desc_item = self.transactions_table.item(row, 1)
            category_item = self.transactions_table.item(row, 2)
            account_item = self.transactions_table.item(row, 3)
            type_item = self.transactions_table.item(row, 4)
            amount_item = self.transactions_table.item(row, 5)
            
            # Check if all required items exist
            print(f"[DEBUG] on_transaction_cell_changed: Checking if all table items exist...")
            if not all([date_item, desc_item, category_item, account_item, type_item, amount_item]):
                print(f"[ERROR] on_transaction_cell_changed: Missing table items for row {row}")
                return
            
            current_date = date_item.text() if date_item else ""
            current_desc = desc_item.text() if desc_item else ""
            current_category = category_item.text() if category_item else ""
            current_account = account_item.text() if account_item else ""
            current_type_text = type_item.text() if type_item else ""
            current_amount_text = amount_item.text() if amount_item else ""
            print(f"[DEBUG] on_transaction_cell_changed: Current values - Date: {current_date}, Desc: {current_desc}, Category: {current_category}, Account: {current_account}, Type: {current_type_text}, Amount: {current_amount_text}")
            
            # Initialize current_amount with the original value
            current_amount = original_tx['amount']
            
            # Validate Date if it was changed
            if column == 0:  # Date column
                print(f"[DEBUG] on_transaction_cell_changed: Validating date: {current_date}")
                try:
                    # Try to parse the date to validate format
                    QDate.fromString(current_date, 'yyyy-MM-dd')
                    print(f"[DEBUG] on_transaction_cell_changed: Date validation passed")
                except:
                    print(f"[ERROR] on_transaction_cell_changed: Invalid date format: {current_date}")
                    QMessageBox.warning(self, "Invalid Date", "Please enter a valid date in YYYY-MM-DD format")
                    # Restore original value
                    original_date = datetime.fromisoformat(original_tx['timestamp']).strftime('%Y-%m-%d')
                    if date_item is not None:
                        date_item.setText(original_date)
                    return
            
            # Validate Type if it was changed
            if column == 4:  # Type column
                print(f"[DEBUG] on_transaction_cell_changed: Validating type: {current_type_text}")
                is_valid, error_msg = self.validate_transaction_type(current_type_text)
                if not is_valid:
                    print(f"[ERROR] on_transaction_cell_changed: Type validation failed: {error_msg}")
                    QMessageBox.warning(self, "Invalid Type", error_msg)
                    # Restore original value
                    if original_tx['type'] == 'in':
                        original_type_text = 'Income'
                    elif original_tx['type'] == 'loan_payment':
                        original_type_text = 'Loan Payment'
                    else:
                        original_type_text = 'Expense'
                    if type_item is not None:
                        type_item.setText(original_type_text)
                    return
            
            # Validate Account if it was changed
            if column == 3:  # Account column
                print(f"[DEBUG] on_transaction_cell_changed: Validating account: {current_account}")
                is_valid, error_msg = self.validate_account_name(current_account)
                if not is_valid:
                    print(f"[ERROR] on_transaction_cell_changed: Account validation failed: {error_msg}")
                    QMessageBox.warning(self, "Invalid Account", error_msg)
                    # Restore original value
                    if account_item is not None:
                        account_item.setText(original_tx['account'])
                    return
            
            # Validate amount if it was changed
            if column == 5:  # Amount column
                print(f"[DEBUG] on_transaction_cell_changed: Validating amount: {current_amount_text}")
                try:
                    current_amount = float(current_amount_text)
                    if current_amount <= 0:
                        print(f"[ERROR] on_transaction_cell_changed: Amount validation failed - must be > 0")
                        QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than 0")
                        # Restore original value
                        if amount_item is not None:
                            amount_item.setText(f'{original_tx["amount"]:.2f}')
                        return
                    print(f"[DEBUG] on_transaction_cell_changed: Amount validation passed: {current_amount}")
                except ValueError:
                    print(f"[ERROR] on_transaction_cell_changed: Amount validation failed - not a number: {current_amount_text}")
                    QMessageBox.warning(self, "Invalid Amount", "Please enter a valid number for the amount")
                    # Restore original value
                    if amount_item is not None:
                        amount_item.setText(f'{original_tx["amount"]:.2f}')
                    return
        except Exception as e:
            print(f"[ERROR] on_transaction_cell_changed: Exception in validation section: {e}")
            import traceback
            traceback.print_exc()
            return
        finally:
            # Always reset the signal processing flag
            self._signal_processing = False
        
        # Convert type text to internal format
        print(f"[DEBUG] on_transaction_cell_changed: Converting type text to internal format")
        if current_type_text == 'Income':
            current_type = 'in'
        elif current_type_text == 'Loan Payment':
            current_type = 'loan_payment'
        else:
            current_type = 'out'
        
        # Check if anything actually changed
        print(f"[DEBUG] on_transaction_cell_changed: Checking if values changed...")
        changed = False
        changes = []
        
        # Compare date
        original_date = datetime.fromisoformat(original_tx['timestamp']).strftime('%Y-%m-%d')
        if current_date != original_date:
            changed = True
            changes.append(f"Date: '{original_date}' → '{current_date}'")
            print(f"[DEBUG] on_transaction_cell_changed: Date changed")
        
        if current_desc != original_tx['desc']:
            changed = True
            changes.append(f"Description: '{original_tx['desc']}' → '{current_desc}'")
            print(f"[DEBUG] on_transaction_cell_changed: Description changed")
        
        if current_category != original_tx.get('category', 'N/A'):
            changed = True
            changes.append(f"Category: '{original_tx.get('category', 'N/A')}' → '{current_category}'")
            print(f"[DEBUG] on_transaction_cell_changed: Category changed")
        
        if current_account != original_tx['account']:
            changed = True
            changes.append(f"Account: '{original_tx['account']}' → '{current_account}'")
            print(f"[DEBUG] on_transaction_cell_changed: Account changed")
        
        if current_type != original_tx['type']:
            changed = True
            if original_tx['type'] == 'in':
                original_type_text = 'Income'
            elif original_tx['type'] == 'loan_payment':
                original_type_text = 'Loan Payment'
            else:
                original_type_text = 'Expense'
            changes.append(f"Type: '{original_type_text}' → '{current_type_text}'")
            print(f"[DEBUG] on_transaction_cell_changed: Type changed")
        
        if column == 5 and current_amount != original_tx['amount']:
            changed = True
            changes.append(f"Amount: ${original_tx['amount']:.2f} → ${current_amount:.2f}")
            print(f"[DEBUG] on_transaction_cell_changed: Amount changed")
        
        # If nothing changed, return
        if not changed:
            print(f"[DEBUG] on_transaction_cell_changed: No changes detected, returning")
            return
        
        print(f"[DEBUG] on_transaction_cell_changed: Changes detected: {changes}")
        
        # Show confirmation dialog
        change_details = "\n".join(changes)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("Confirm Transaction Changes")
        msg.setText("Are you sure you want to modify this transaction?")
        msg.setDetailedText(f"Transaction: {original_tx['desc']}\n\nChanges:\n{change_details}")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        reply = msg.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            print(f"[DEBUG] on_transaction_cell_changed: User confirmed changes, applying...")
            # Apply the changes
            self.apply_transaction_changes(row, current_date, current_desc, current_category, current_account, current_type, current_amount)
        else:
            print(f"[DEBUG] on_transaction_cell_changed: User cancelled changes, restoring original values")
            # Restore original values
            self.restore_original_transaction_values(row)
    
    def apply_transaction_changes(self, row, new_date, new_desc, new_category, new_account, new_type, new_amount):
        """Apply changes to a transaction"""
        print(f"[DEBUG] apply_transaction_changes: Starting for row {row}")
        try:
            original_tx = self.original_transactions[row]
            print(f"[DEBUG] apply_transaction_changes: Original transaction: {original_tx.get('desc', 'N/A')}")
            
            # Check if account changed - this requires special handling
            account_changed = new_account != original_tx['account']
            
            if account_changed:
                print(f"[DEBUG] apply_transaction_changes: Account changed from '{original_tx['account']}' to '{new_account}'")
                
                # We need to:
                # 1. Remove the transaction from the original account (reverses its balance effect)
                # 2. Add the new transaction to the new account
                
                # Step 1: Remove original transaction (this reverses the balance effect on original account)
                print(f"[DEBUG] apply_transaction_changes: Removing transaction from original account '{original_tx['account']}'")
                self.bank.remove_transaction(original_tx)
                
                # Step 2: Add new transaction to new account
                print(f"[DEBUG] apply_transaction_changes: Adding transaction to new account '{new_account}'")
                
                # Convert timestamp to date format
                from datetime import datetime
                if new_date != datetime.fromisoformat(original_tx['timestamp']).strftime('%Y-%m-%d'):
                    # Use new date
                    date_str = new_date
                else:
                    # Use original date
                    timestamp_dt = datetime.fromisoformat(original_tx['timestamp'])
                    date_str = timestamp_dt.strftime('%Y-%m-%d')
                
                # Get account_id for new account
                new_account_id = None
                try:
                    user_accounts = self.bank.get_user_bank_accounts(original_tx['user_id'])
                    for account in user_accounts:
                        if account.account_name == new_account or account.bank_name == new_account:
                            new_account_id = account.account_id
                            break
                    print(f"[DEBUG] apply_transaction_changes: Found new account_id: {new_account_id}")
                except Exception as e:
                    print(f"[WARNING] apply_transaction_changes: Could not find account_id for '{new_account}': {e}")
                
                self.bank.add_transaction(
                    amount=new_amount,
                    desc=new_desc,
                    account=new_account,
                    account_id=new_account_id,
                    type_=new_type,
                    category=new_category,
                    date=date_str,
                    user_id=original_tx['user_id']
                )
                
                print(f"[DEBUG] apply_transaction_changes: Successfully moved transaction from '{original_tx['account']}' to '{new_account}'")
                
            else:
                # Account didn't change, just update the existing transaction
                print(f"[DEBUG] apply_transaction_changes: Account unchanged, updating existing transaction")
                
                # Create updated transaction
                updated_tx = original_tx.copy()
                updated_tx['desc'] = new_desc
                updated_tx['category'] = new_category if new_category != 'N/A' else None
                updated_tx['account'] = new_account
                updated_tx['type'] = new_type
                updated_tx['amount'] = new_amount
                
                # Update timestamp if date changed
                original_date_str = original_tx['timestamp'].split('T')[0]
                if new_date != original_date_str:
                    print(f"[DEBUG] apply_transaction_changes: Date changed from {original_date_str} to {new_date}")
                    from datetime import datetime
                    original_dt = datetime.fromisoformat(original_tx['timestamp'])
                    new_date_obj = QDate.fromString(new_date, 'yyyy-MM-dd').toPyDate()
                    updated_timestamp = datetime.combine(new_date_obj, original_dt.time())
                    updated_tx['timestamp'] = updated_timestamp.isoformat()
                    print(f"[DEBUG] apply_transaction_changes: New timestamp: {updated_tx['timestamp']}")
                
                # Update in the bank system by removing old and adding new
                print(f"[DEBUG] apply_transaction_changes: Removing old transaction...")
                self.bank.remove_transaction(original_tx)
                
                # Convert timestamp to date format expected by add_transaction
                from datetime import datetime
                timestamp_dt = datetime.fromisoformat(updated_tx['timestamp'])
                date_str = timestamp_dt.strftime('%Y-%m-%d')
                
                print(f"[DEBUG] apply_transaction_changes: Adding updated transaction...")
                self.bank.add_transaction(
                    amount=updated_tx['amount'],
                    desc=updated_tx['desc'],
                    account=updated_tx['account'],
                    account_id=updated_tx.get('account_id'),
                    type_=updated_tx['type'],
                    category=updated_tx['category'],
                    date=date_str,
                    user_id=updated_tx['user_id'],
                    identifier=updated_tx.get('identifier')  # Preserve original identifier if possible
                )
            
            # Refresh the data to show changes
            print(f"[DEBUG] apply_transaction_changes: Refreshing data...")
            self.refresh_data()
            
            success_message = "Transaction updated successfully!"
            if account_changed:
                success_message += f"\n\nMoved from '{original_tx['account']}' to '{new_account}'"
            
            QMessageBox.information(self, "Success", success_message)
            print(f"[DEBUG] apply_transaction_changes: Transaction updated successfully")
            
        except Exception as e:
            print(f"[ERROR] apply_transaction_changes: Error applying transaction changes: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to update transaction: {str(e)}")
            # Refresh to restore original state
            self.refresh_data()
    
    def restore_original_transaction_values(self, row):
        """Restore original values for a transaction row"""
        print(f"[DEBUG] restore_original_transaction_values: Restoring values for row {row}")
        try:
            if row not in self.original_transactions:
                print(f"[WARNING] restore_original_transaction_values: No original transaction found for row {row}")
                return
            
            original_tx = self.original_transactions[row]
            print(f"[DEBUG] restore_original_transaction_values: Original transaction: {original_tx.get('desc', 'N/A')}")
            
            # Temporarily disconnect signal to avoid triggering during restoration
            print("[DEBUG] restore_original_transaction_values: Disconnecting signal...")
            try:
                self.transactions_table.itemChanged.disconnect()
                print("[DEBUG] restore_original_transaction_values: Signal disconnected")
            except TypeError:
                print("[DEBUG] restore_original_transaction_values: Signal was not connected")
            except Exception as e:
                print(f"[ERROR] restore_original_transaction_values: Error disconnecting signal: {e}")
            
            # Restore values
            print("[DEBUG] restore_original_transaction_values: Restoring table values...")
            original_date = datetime.fromisoformat(original_tx['timestamp']).strftime('%Y-%m-%d')
            
            # Safe table item restoration
            item = self.transactions_table.item(row, 0)
            if item is not None:
                item.setText(original_date)
            
            item = self.transactions_table.item(row, 1)
            if item is not None:
                item.setText(original_tx['desc'])
            
            item = self.transactions_table.item(row, 2)
            if item is not None:
                item.setText(original_tx.get('category', 'N/A'))
            
            item = self.transactions_table.item(row, 3)
            if item is not None:
                item.setText(original_tx['account'])
            
            if original_tx['type'] == 'in':
                original_type_text = 'Income'
            elif original_tx['type'] == 'loan_payment':
                original_type_text = 'Loan Payment'
            else:
                original_type_text = 'Expense'
            
            item = self.transactions_table.item(row, 4)
            if item is not None:
                item.setText(original_type_text)
            
            item = self.transactions_table.item(row, 5)
            if item is not None:
                item.setText(f'{original_tx["amount"]:.2f}')
            # Editors will open on user interaction; no programmatic sanity check to avoid UI glitches
                
        except Exception as e:
            print(f"[ERROR] restore_original_transaction_values: Error restoring values: {e}")
            import traceback
            traceback.print_exc()
    
    def view_transaction_attachments(self, transaction):
        """View attachments for a transaction"""
        attachments = transaction.get('attachments', [])
        
        if not attachments:
            QMessageBox.information(self, 'No Attachments', 'This transaction has no attachments')
            return
        
        from src.attachment_manager import AttachmentManager
        attachment_manager = AttachmentManager()
        
        dialog = AttachmentViewerDialog(
            self,
            attachments=attachments,
            current_index=0,
            attachment_manager=attachment_manager
        )
        dialog.exec()
    
    def delete_transaction(self, transaction):
        """Delete a transaction with options for handling account balance"""
        # Create custom dialog with three options
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("Delete Transaction")
        msg.setText(f"How would you like to delete this transaction?")
        msg.setDetailedText(f"Transaction: {transaction['desc']}\n"
                           f"Account: {transaction['account']}\n"
                           f"Amount: ${transaction['amount']:.2f}\n"
                           f"Type: {'Income' if transaction['type'] == 'in' else ('Loan Payment' if transaction['type'] == 'loan_payment' else 'Expense')}")
        
        # Add custom buttons
        reverse_btn = msg.addButton("Reverse Effect on Account", QMessageBox.ButtonRole.AcceptRole)
        if reverse_btn is not None:
            reverse_btn.setToolTip("Remove transaction and correct the account balance (Recommended)")
        
        delete_only_btn = msg.addButton("Delete Record Only", QMessageBox.ButtonRole.DestructiveRole)  
        if delete_only_btn is not None:
            delete_only_btn.setToolTip("Remove transaction record but keep account balance unchanged")
        
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        if cancel_btn is not None:
            cancel_btn.setToolTip("Don't delete anything")
        
        msg.setDefaultButton(reverse_btn)  # Make "Reverse Effect" the default
        
        # Show dialog and get result
        msg.exec()
        clicked_button = msg.clickedButton()
        
        if clicked_button == reverse_btn:
            # Reverse effect on account (recommended approach)
            try:
                print(f"[DEBUG] delete_transaction: Reversing effect and removing transaction '{transaction['desc']}'")
                self.bank.remove_transaction(transaction)
                self.refresh_data()
                QMessageBox.information(self, "Success", 
                                      f"Transaction deleted and account balance corrected.\n\n"
                                      f"Account '{transaction['account']}' balance has been updated.")
            except Exception as e:
                print(f"[ERROR] delete_transaction: Error removing transaction: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete transaction: {str(e)}")
                
        elif clicked_button == delete_only_btn:
            # Delete record only, no balance changes
            try:
                print(f"[DEBUG] delete_transaction: Deleting record only for '{transaction['desc']}'")
                
                # We need to implement a method that removes just the record without affecting balance
                # For now, we'll use the standard remove but warn the user
                confirmation = QMessageBox.question(self, "Confirm Record-Only Delete",
                    "⚠️ WARNING: This will remove the transaction record but may affect account balance calculations.\n\n"
                    "Are you sure you want to proceed?\n\n"
                    "Recommended: Use 'Reverse Effect on Account' instead.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
                
                if confirmation == QMessageBox.StandardButton.Yes:
                    # Remove the transaction (this will still affect balance since that's how the system works)
                    self.bank.remove_transaction(transaction)
                    self.refresh_data()
                    QMessageBox.warning(self, "Record Deleted", 
                                      f"Transaction record deleted.\n\n"
                                      f"Note: Account balance may have been affected.")
                else:
                    print(f"[DEBUG] delete_transaction: User cancelled record-only delete")
                    
            except Exception as e:
                print(f"[ERROR] delete_transaction: Error deleting record: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete transaction record: {str(e)}")
                
        else:  # Cancel button or dialog closed
            print(f"[DEBUG] delete_transaction: User cancelled deletion")
            return
    
    def delete_recurring_transaction(self, recurring_tx):
        """Delete a recurring transaction"""
        reply = QMessageBox.question(self, 'Confirm Delete', 
                                   f'Delete recurring transaction: {recurring_tx["desc"]}?')
        if reply == QMessageBox.StandardButton.Yes:
            self.bank.remove_recurring_transaction(recurring_tx['identifier'])
            self.refresh_data()
    
    def pause_recurring_transaction(self, recurring_tx):
        """Pause a recurring transaction"""
        try:
            # Find and update the recurring transaction
            for i, rt in enumerate(self.bank.recurring_transactions):
                if rt['identifier'] == recurring_tx['identifier']:
                    from src.bank import RecurringTransaction
                    recurring_obj = RecurringTransaction.from_dict(rt)
                    recurring_obj.pause()
                    self.bank.recurring_transactions[i] = recurring_obj.to_dict()
                    self.bank.save_recurring()
                    break
            self.refresh_data()
            QMessageBox.information(self, 'Success', f'Paused: {recurring_tx["desc"]}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to pause: {e}')
    
    def resume_recurring_transaction(self, recurring_tx):
        """Resume a paused recurring transaction"""
        try:
            # Find and update the recurring transaction
            for i, rt in enumerate(self.bank.recurring_transactions):
                if rt['identifier'] == recurring_tx['identifier']:
                    from src.bank import RecurringTransaction
                    recurring_obj = RecurringTransaction.from_dict(rt)
                    recurring_obj.resume()
                    self.bank.recurring_transactions[i] = recurring_obj.to_dict()
                    self.bank.save_recurring()
                    break
            self.refresh_data()
            QMessageBox.information(self, 'Success', f'Resumed: {recurring_tx["desc"]}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to resume: {e}')
    
    def skip_next_recurring(self, recurring_tx):
        """Mark recurring transaction to skip next occurrence"""
        try:
            # Find and update the recurring transaction
            for i, rt in enumerate(self.bank.recurring_transactions):
                if rt['identifier'] == recurring_tx['identifier']:
                    from src.bank import RecurringTransaction
                    recurring_obj = RecurringTransaction.from_dict(rt)
                    recurring_obj.mark_skip_next()
                    self.bank.recurring_transactions[i] = recurring_obj.to_dict()
                    self.bank.save_recurring()
                    break
            self.refresh_data()
            QMessageBox.information(self, 'Skipped', f'Next occurrence will be skipped: {recurring_tx["desc"]}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to skip: {e}')
    
    def process_recurring_now(self, recurring_tx):
        """Process a recurring transaction immediately"""
        reply = QMessageBox.question(self, 'Confirm Process', 
                                   f'Process this recurring transaction now?\n\n{recurring_tx["desc"]}')
        if reply == QMessageBox.StandardButton.Yes:
            try:
                count = self.bank.process_recurring_transactions(force_identifier=recurring_tx['identifier'])
                self.refresh_data()
                QMessageBox.information(self, 'Success', f'Processed: {recurring_tx["desc"]}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to process: {e}')
    
    def show_recurring_history(self, recurring_tx):
        """Show history of instances created by this recurring transaction"""
        try:
            dialog = RecurringHistoryDialog(recurring_tx, self.bank, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to show history: {e}')
    
    def show_recurring_calendar(self):
        """Show 30-day calendar preview of upcoming recurring transactions"""
        try:
            dialog = RecurringCalendarDialog(self.bank, self.current_user_id, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to show calendar: {e}')
            import traceback
            traceback.print_exc()
    
    def show_upcoming_recurring(self):
        """Show notifications for upcoming recurring transactions in next 7 days"""
        try:
            dialog = UpcomingRecurringDialog(self.bank, self.current_user_id, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to show upcoming: {e}')
    
    def on_recurring_cell_changed(self, row, column):
        """Handle when a recurring transaction cell is edited"""
        print(f"[DEBUG] on_recurring_cell_changed: Cell changed - Row: {row}, Column: {column}")
        
        # Prevent recursive signal calls
        if hasattr(self, '_recurring_signal_processing') and self._recurring_signal_processing:
            print("[DEBUG] on_recurring_cell_changed: Recursive call detected, ignoring")
            return

        self._recurring_signal_processing = True
        
        try:
            # Get the recurring transaction item
            recurring_txs = self.bank.list_recurring_transactions(self.current_user_id)
            if row >= len(recurring_txs):
                print(f"[ERROR] on_recurring_cell_changed: Row {row} out of range")
                return
            
            recurring_tx = recurring_txs[row]
            print(f"[DEBUG] on_recurring_cell_changed: Processing recurring transaction: {recurring_tx['desc']}")
            
            # Get current values from table
            desc_item = self.recurring_table.item(row, 0)
            category_item = self.recurring_table.item(row, 1)
            account_item = self.recurring_table.item(row, 2)
            type_item = self.recurring_table.item(row, 3)
            amount_item = self.recurring_table.item(row, 4)
            frequency_item = self.recurring_table.item(row, 5)
            
            if not all([desc_item, category_item, account_item, type_item, amount_item, frequency_item]):
                print(f"[ERROR] on_recurring_cell_changed: Missing table items for row {row}")
                return
            
            # Extract current values
            current_desc = desc_item.text() if desc_item else ""
            current_category = category_item.text() if category_item else ""
            current_account = account_item.text() if account_item else ""
            current_type_text = type_item.text() if type_item else ""
            current_amount_text = amount_item.text() if amount_item else ""
            current_frequency = frequency_item.text().lower() if frequency_item else ""
            
            # Validate amount if it was changed
            if column == 4:  # Amount column
                try:
                    current_amount = float(current_amount_text)
                    if current_amount <= 0:
                        QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than 0")
                        if amount_item is not None:
                            amount_item.setText(f'${recurring_tx["amount"]:.2f}')
                        return
                except ValueError:
                    QMessageBox.warning(self, "Invalid Amount", "Please enter a valid number for the amount")
                    if amount_item is not None:
                        amount_item.setText(f'${recurring_tx["amount"]:.2f}')
                    return
            else:
                current_amount = recurring_tx['amount']
            
            # Convert type text to internal format
            if current_type_text == 'Income':
                current_type = 'in'
            elif current_type_text == 'Loan Payment':
                current_type = 'loan_payment'
            else:
                current_type = 'out'
            
            # Show confirmation dialog
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setWindowTitle("Confirm Recurring Transaction Changes")
            msg.setText(f"Update recurring transaction: {recurring_tx['desc']}?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                # Update the recurring transaction
                updated_data = {
                    'identifier': recurring_tx['identifier'],
                    'desc': current_desc,
                    'category': current_category,
                    'account': current_account,
                    'type': current_type,
                    'amount': current_amount,
                    'frequency': current_frequency,
                    'start_date': recurring_tx['start_date'],
                    'end_date': recurring_tx.get('end_date'),
                    'user_id': recurring_tx['user_id'],
                    'last_processed': recurring_tx.get('last_processed'),
                    'active': recurring_tx.get('active', True)
                }
                
                # Find and update the recurring transaction in the bank
                for i, rt in enumerate(self.bank.recurring_transactions):
                    if rt['identifier'] == recurring_tx['identifier']:
                        self.bank.recurring_transactions[i] = updated_data
                        break
                
                self.bank.save_recurring()
                print(f"[DEBUG] on_recurring_cell_changed: Recurring transaction updated successfully")
                
                # Refresh the display with signal blocking
                self.update_recurring_table_with_signal_block()
            else:
                # Restore original values
                print(f"[DEBUG] on_recurring_cell_changed: User cancelled, restoring original values")
                self.update_recurring_table_with_signal_block()
                
        except Exception as e:
            print(f"[ERROR] on_recurring_cell_changed: Error handling cell change: {e}")
            import traceback
            traceback.print_exc()
            # Restore table on error
            self.update_recurring_table_with_signal_block()
        finally:
            # Always reset the signal processing flag
            self._recurring_signal_processing = False
    
    def update_recurring_table_with_signal_block(self):
        """Update recurring table while blocking cellChanged signals"""
        try:
            # Temporarily block signals to prevent recursive calls
            self.recurring_table.blockSignals(True)
            self.update_recurring_table()
        except Exception as e:
            print(f"[ERROR] update_recurring_table_with_signal_block: {e}")
        finally:
            # Always unblock signals
            self.recurring_table.blockSignals(False)
    
    def on_loan_cell_changed(self, row, column):
        """Handle when a loan cell is edited"""
        print(f"[DEBUG] on_loan_cell_changed: Cell changed - Row: {row}, Column: {column}")
        
        # Prevent recursive signal calls
        if hasattr(self, '_loan_signal_processing') and self._loan_signal_processing:
            print("[DEBUG] on_loan_cell_changed: Recursive call detected, ignoring")
            return

        self._loan_signal_processing = True
        
        try:
            # Get the loan items
            loans = self.bank.list_loans(self.current_user_id)
            if row >= len(loans):
                print(f"[ERROR] on_loan_cell_changed: Row {row} out of range")
                return
            
            loan = loans[row]
            print(f"[DEBUG] on_loan_cell_changed: Processing loan: {loan.desc}")
            
            # Only allow editing of certain columns
            editable_columns = [0, 1, 2, 3, 4, 5, 7, 8, 9]  # Description, Accounts, Principal, Rate, Payment, Frequency, Next Due, Status
            if column not in editable_columns:
                print(f"[DEBUG] on_loan_cell_changed: Column {column} is not editable")
                return
            
            # Get current values from table
            desc_item = self.loans_table.item(row, 0)
            loan_account_item = self.loans_table.item(row, 1)
            pay_from_item = self.loans_table.item(row, 2)
            principal_item = self.loans_table.item(row, 3)
            rate_item = self.loans_table.item(row, 4)
            payment_item = self.loans_table.item(row, 5)
            frequency_item = self.loans_table.item(row, 7)
            next_due_item = self.loans_table.item(row, 8)
            status_item = self.loans_table.item(row, 9)
            
            if not all([desc_item, loan_account_item, pay_from_item, principal_item, rate_item, payment_item, frequency_item, next_due_item, status_item]):
                print(f"[ERROR] on_loan_cell_changed: Missing table items for row {row}")
                return
            
            # Extract current values
            current_desc = desc_item.text() if desc_item else ""
            current_loan_account = loan_account_item.text() if loan_account_item else ""
            current_pay_from = pay_from_item.text() if pay_from_item else ""
            current_principal_text = principal_item.text().replace('$', '').replace(',', '') if principal_item else ""
            current_rate_text = rate_item.text().replace('%', '') if rate_item else ""
            current_payment_text = payment_item.text().replace('$', '').replace(',', '') if payment_item else ""
            current_frequency = frequency_item.text().lower() if frequency_item else ""
            current_next_due = next_due_item.text() if next_due_item else ""
            current_status = status_item.text() if status_item else ""
            
            # Validate numeric fields
            try:
                current_principal = float(current_principal_text) if current_principal_text else loan.principal
                current_rate = float(current_rate_text) if current_rate_text else loan.annual_rate * 100
                current_payment = float(current_payment_text) if current_payment_text else loan.payment_amount
                
                if column == 3 and current_principal <= 0:  # Principal
                    QMessageBox.warning(self, "Invalid Principal", "Principal must be greater than 0")
                    self.restore_loan_table_value(row, 3, f"${loan.principal:,.2f}")
                    return
                    
                if column == 4 and (current_rate < 0 or current_rate > 100):  # Rate
                    QMessageBox.warning(self, "Invalid Rate", "Rate must be between 0% and 100%")
                    self.restore_loan_table_value(row, 4, f"{loan.annual_rate*100:.2f}%")
                    return
                    
                if column == 5 and current_payment <= 0:  # Payment
                    QMessageBox.warning(self, "Invalid Payment", "Payment must be greater than 0")
                    self.restore_loan_table_value(row, 5, f"${loan.payment_amount:,.2f}")
                    return
                    
            except ValueError:
                QMessageBox.warning(self, "Invalid Number", "Please enter a valid number")
                # Restore original value based on column
                if column == 3:
                    self.restore_loan_table_value(row, 3, f"${loan.principal:,.2f}")
                elif column == 4:
                    self.restore_loan_table_value(row, 4, f"{loan.annual_rate*100:.2f}%")
                elif column == 5:
                    self.restore_loan_table_value(row, 5, f"${loan.payment_amount:,.2f}")
                return
            
            # Show confirmation dialog
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setWindowTitle("Confirm Loan Changes")
            msg.setText(f"Update loan: {loan.desc}?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            if msg.exec() == QMessageBox.StandardButton.Yes:
                print(f"[DEBUG] on_loan_cell_changed: User confirmed changes, updating loan")
                
                # Update loan attributes
                loan.desc = current_desc
                loan.account_name = current_loan_account
                if hasattr(loan, 'pay_from_account_name'):
                    loan.pay_from_account_name = current_pay_from
                loan.principal = current_principal
                loan.annual_rate = current_rate / 100  # Convert percentage back to decimal
                loan.payment_amount = current_payment
                loan.frequency = current_frequency
                
                # Handle status changes
                if current_status.lower() == 'completed':
                    loan.remaining_principal = 0
                    loan.active = False
                elif current_status.lower() == 'inactive':
                    loan.active = False
                else:
                    loan.active = True
                
                # Save changes (this would need a proper update method in the bank)
                # For now, just refresh the display
                print(f"[DEBUG] on_loan_cell_changed: Loan updated successfully")
                
                # Refresh the display with signal blocking
                self.update_loans_table_with_signal_block()
            else:
                # Restore original values
                print(f"[DEBUG] on_loan_cell_changed: User cancelled, restoring original values")
                self.update_loans_table_with_signal_block()
                
        except Exception as e:
            print(f"[ERROR] on_loan_cell_changed: Error handling cell change: {e}")
            import traceback
            traceback.print_exc()
            # Restore table on error
            self.update_loans_table_with_signal_block()
        finally:
            # Always reset the signal processing flag
            self._loan_signal_processing = False
    
    def restore_loan_table_value(self, row, column, value):
        """Restore a single value in the loans table without triggering signals"""
        try:
            # Temporarily block signals
            self.loans_table.blockSignals(True)
            item = self.loans_table.item(row, column)
            if item:
                item.setText(value)
        except Exception as e:
            print(f"[ERROR] restore_loan_table_value: {e}")
        finally:
            # Always unblock signals
            self.loans_table.blockSignals(False)
    
    def update_loans_table_with_signal_block(self):
        """Update loans table while blocking cellChanged signals"""
        try:
            # Temporarily block signals to prevent recursive calls
            self.loans_table.blockSignals(True)
            self.update_loans_table()
        except Exception as e:
            print(f"[ERROR] update_loans_table_with_signal_block: {e}")
        finally:
            # Always unblock signals
            self.loans_table.blockSignals(False)
    
    def filter_transactions(self):
        """Filter transactions based on multiple criteria"""
        search_text = self.search_edit.text().lower()
        start_date = self.filter_start_date.date().toPyDate()
        end_date = self.filter_end_date.date().toPyDate()
        min_amount = self.filter_min_amount.value()
        max_amount = self.filter_max_amount.value()
        selected_type = self.filter_type.currentText()
        selected_account = self.filter_account.currentText()
        selected_category = self.filter_category.currentText()
        selected_bank = self.filter_bank.currentText()
        
        visible_count = 0
        total_count = self.transactions_table.rowCount()
        
        for row in range(total_count):
            show_row = True
            
            # Text search filter
            if search_text:
                match = False
                for col in range(self.transactions_table.columnCount() - 1):  # Exclude actions column
                    item = self.transactions_table.item(row, col)
                    if item and search_text in item.text().lower():
                        match = True
                        break
                if not match:
                    show_row = False
            
            # Date range filter
            if show_row:
                date_item = self.transactions_table.item(row, 0)
                if date_item:
                    try:
                        row_date = datetime.strptime(date_item.text(), '%Y-%m-%d').date()
                        if row_date < start_date or row_date > end_date:
                            show_row = False
                    except ValueError:
                        show_row = False
            
            # Amount range filter
            if show_row:
                amount_item = self.transactions_table.item(row, 5)
                if amount_item:
                    try:
                        amount = float(amount_item.text())
                        if amount < min_amount or amount > max_amount:
                            show_row = False
                    except ValueError:
                        show_row = False
            
            # Type filter
            if show_row and selected_type != "All Types":
                type_item = self.transactions_table.item(row, 4)
                if type_item and type_item.text() != selected_type:
                    show_row = False
            
            # Account filter
            if show_row and selected_account != "All Accounts":
                account_item = self.transactions_table.item(row, 3)
                if account_item and selected_account not in account_item.text():
                    show_row = False
            
            # Category filter
            if show_row and selected_category != "All Categories":
                category_item = self.transactions_table.item(row, 2)
                if category_item and category_item.text() != selected_category:
                    show_row = False
            
            # Bank filter
            if show_row and selected_bank != "All Banks":
                account_item = self.transactions_table.item(row, 3)
                if account_item and selected_bank not in account_item.text():
                    show_row = False
            
            self.transactions_table.setRowHidden(row, not show_row)
            if show_row:
                visible_count += 1
        
        # Update filter summary
        if visible_count == total_count:
            self.filter_summary_label.setText("Showing all transactions")
        else:
            self.filter_summary_label.setText(f"Showing {visible_count} of {total_count} transactions")
    
    def populate_filter_options(self):
        """Populate filter dropdown options based on current transactions"""
        try:
            # Get all unique values for filter options
            accounts = set()
            categories = set()
            banks = set()
            
            for row in range(self.transactions_table.rowCount()):
                # Account filter options
                account_item = self.transactions_table.item(row, 3)
                if account_item:
                    account_text = account_item.text()
                    accounts.add(account_text)
                    # Extract bank name (before the first " - ")
                    if " - " in account_text:
                        bank_name = account_text.split(" - ")[0]
                        banks.add(bank_name)
                
                # Category filter options
                category_item = self.transactions_table.item(row, 2)
                if category_item:
                    categories.add(category_item.text())
            
            # Update account filter
            current_account = self.filter_account.currentText()
            self.filter_account.clear()
            self.filter_account.addItem("All Accounts")
            for account in sorted(accounts):
                self.filter_account.addItem(account)
            # Restore selection if still valid
            index = self.filter_account.findText(current_account)
            if index >= 0:
                self.filter_account.setCurrentIndex(index)
            
            # Update category filter
            current_category = self.filter_category.currentText()
            self.filter_category.clear()
            self.filter_category.addItem("All Categories")
            for category in sorted(categories):
                if category and category != "N/A":
                    self.filter_category.addItem(category)
            # Restore selection if still valid
            index = self.filter_category.findText(current_category)
            if index >= 0:
                self.filter_category.setCurrentIndex(index)
            
            # Update bank filter
            current_bank = self.filter_bank.currentText()
            self.filter_bank.clear()
            self.filter_bank.addItem("All Banks")
            for bank in sorted(banks):
                if bank:
                    self.filter_bank.addItem(bank)
            # Restore selection if still valid
            index = self.filter_bank.findText(current_bank)
            if index >= 0:
                self.filter_bank.setCurrentIndex(index)
                
        except Exception as e:
            print(f"[WARNING] Error populating filter options: {e}")
    
    def clear_filters(self):
        """Clear all filters and show all transactions"""
        self.search_edit.clear()
        self.filter_start_date.setDate(QDate.currentDate().addDays(-30))
        self.filter_end_date.setDate(QDate.currentDate())
        self.filter_min_amount.setValue(0.0)
        self.filter_max_amount.setValue(999999.99)
        self.filter_type.setCurrentIndex(0)
        self.filter_account.setCurrentIndex(0)
        self.filter_category.setCurrentIndex(0)
        self.filter_bank.setCurrentIndex(0)
        self.filter_transactions()
    
    def export_filtered_transactions(self):
        """Export currently filtered transactions to CSV"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            # Get visible transactions
            visible_transactions = []
            headers = []
            
            # Get headers
            for col in range(self.transactions_table.columnCount() - 1):  # Exclude actions column
                header_item = self.transactions_table.horizontalHeaderItem(col)
                if header_item is not None:
                    headers.append(header_item.text())
                else:
                    headers.append(f"Column {col}")
            
            # Get visible rows
            for row in range(self.transactions_table.rowCount()):
                if not self.transactions_table.isRowHidden(row):
                    row_data = []
                    for col in range(self.transactions_table.columnCount() - 1):
                        item = self.transactions_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    visible_transactions.append(row_data)
            
            if not visible_transactions:
                QMessageBox.information(self, "Export", "No transactions to export.")
                return
            
            # Get export file path
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Export Filtered Transactions", 
                f"filtered_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
                    writer.writerows(visible_transactions)
                
                QMessageBox.information(self, "Export Complete", 
                                      f"Exported {len(visible_transactions)} transactions to {file_path}")
        
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export transactions: {e}")

    # ===== Loans Tab Logic =====
    def update_loans_table(self):
        """Populate the loans table with current user's loans."""
        print("[DEBUG] update_loans_table: Starting loans table update...")
        try:
            # Block signals during table population to prevent triggering cellChanged
            self.loans_table.blockSignals(True)
            print("[DEBUG] update_loans_table: Signals blocked")
            
            loans = self.bank.list_loans(self.current_user_id)
            self.loans_table.setRowCount(len(loans))
            print(f"[DEBUG] update_loans_table: Processing {len(loans)} loans")
            
            for row, loan in enumerate(loans):
                # Description
                self.loans_table.setItem(row, 0, QTableWidgetItem(loan.desc))
                # Loan Account display
                account_display = loan.account_name or 'Unassigned'
                self.loans_table.setItem(row, 1, QTableWidgetItem(account_display))
                # Pay From Account
                pay_from_text = getattr(loan, 'pay_from_account_name', 'Not Set') or 'Not Set'
                self.loans_table.setItem(row, 2, QTableWidgetItem(pay_from_text))
                # Principal
                self.loans_table.setItem(row, 3, QTableWidgetItem(f"${loan.principal:,.2f}"))
                # Rate
                self.loans_table.setItem(row, 4, QTableWidgetItem(f"{loan.annual_rate*100:.2f}%"))
                # Min Payment
                payment_amount = getattr(loan, 'minimum_payment', getattr(loan, 'payment_amount', 0))
                self.loans_table.setItem(row, 5, QTableWidgetItem(f"${payment_amount:,.2f}"))
                # Remaining
                self.loans_table.setItem(row, 6, QTableWidgetItem(f"${loan.remaining_principal:,.2f}"))
                # Frequency
                self.loans_table.setItem(row, 7, QTableWidgetItem(loan.frequency.title()))
                # Next Due
                try:
                    next_due = loan.get_next_due_date()
                    next_due_str = next_due.strftime('%Y-%m-%d') if next_due else '—'
                except Exception:
                    next_due_str = '—'
                self.loans_table.setItem(row, 8, QTableWidgetItem(next_due_str))
                # Status
                status = 'Completed' if loan.remaining_principal <= 0 or not loan.active else 'Active'
                self.loans_table.setItem(row, 9, QTableWidgetItem(status))

                # Actions
                actions = QWidget()
                h = QHBoxLayout()
                h.setContentsMargins(0, 0, 0, 0)
                
                details_btn = QPushButton('Details')
                details_btn.clicked.connect(lambda checked=False, l=loan: self.view_loan_details(l))
                h.addWidget(details_btn)
                
                remove_btn = QPushButton('Remove')
                remove_btn.clicked.connect(lambda checked=False, ident=loan.identifier: self.remove_loan(ident))
                h.addWidget(remove_btn)
                
                h.addStretch()
                actions.setLayout(h)
                self.loans_table.setCellWidget(row, 10, actions)
        except Exception as e:
            print(f"[ERROR] update_loans_table: {e}")
        finally:
            # Always unblock signals
            self.loans_table.blockSignals(False)
            print("[DEBUG] update_loans_table: Signals unblocked")

    def add_loan(self):
        """Open dialog and add a new loan."""
        dlg = AddLoanDialog(self, self.bank, self.current_user_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if not data['desc']:
                QMessageBox.warning(self, 'Validation', 'Description is required')
                return
            if data['principal'] <= 0 or data['payment_amount'] <= 0:
                QMessageBox.warning(self, 'Validation', 'Principal and payment must be greater than 0')
                return
            try:
                # Add the loan
                loan_result = self.bank.add_loan(
                    principal=data['principal'],
                    annual_rate=data['annual_rate'],
                    payment_amount=data['payment_amount'],
                    desc=data['desc'],
                    account_id=data['account_id'],
                    account_name=data['account_name'],
                    frequency=data['frequency'],
                    start_date=data['start_date'],
                    end_date=data['end_date'],
                    user_id=self.current_user_id,
                    pay_from_account_id=data['pay_from_account_id'],
                    pay_from_account_name=data['pay_from_account_name'],
                    auto_create_account=data['auto_create_account']
                )
                
                # Auto-create recurring payment for the loan
                loan_account_name = loan_result.get('account_name') or data.get('account_name')
                if data['pay_from_account_id'] and loan_account_name:
                    try:
                        recurring_data = {
                            'amount': data['payment_amount'],
                            'desc': f"Loan Payment - {data['desc']}",
                            'pay_from_account_id': data['pay_from_account_id'],
                            'pay_from_account_name': data['pay_from_account_name'],
                            'pay_to_account_name': loan_account_name,  # The loan account (auto-created or existing)
                            'category': 'Loan Payment',
                            'frequency': data['frequency'],
                            'start_date': data['start_date'],
                            'end_date': data['end_date'],
                            'type': 'loan_payment',
                            'user_id': self.current_user_id
                        }
                        
                        recurring_result = self.bank.add_recurring_transaction(
                            amount=recurring_data['amount'],
                            desc=recurring_data['desc'],
                            account=recurring_data['pay_from_account_name'],
                            account_id=recurring_data['pay_from_account_id'],
                            type_=recurring_data['type'],
                            category=recurring_data['category'],
                            frequency=recurring_data['frequency'],
                            start_date=recurring_data['start_date'],
                            end_date=recurring_data['end_date'],
                            user_id=recurring_data['user_id']
                        )
                        
                        print(f"[DEBUG] Auto-created recurring payment for loan: {recurring_result}")
                        
                        # Create success message
                        success_msg = f'Loan "{data["desc"]}" added successfully!'
                        if loan_result.get('auto_created_account'):
                            success_msg += f'\n✓ Auto-created loan account: {loan_account_name}'
                        success_msg += '\n✓ Automatic recurring payment created.'
                        
                        QMessageBox.information(self, 'Loan Added', success_msg)
                    except Exception as e:
                        print(f"[WARNING] Failed to create automatic recurring payment: {e}")
                        
                        # Create partial success message
                        success_msg = f'Loan "{data["desc"]}" added successfully!'
                        if loan_result.get('auto_created_account'):
                            success_msg += f'\n✓ Auto-created loan account: {loan_account_name}'
                        success_msg += f'\n⚠️ However, failed to create automatic recurring payment: {e}'
                        
                        QMessageBox.warning(self, 'Loan Added', success_msg)
                else:
                    # Create basic success message
                    success_msg = f'Loan "{data["desc"]}" added successfully!'
                    if loan_result.get('auto_created_account'):
                        success_msg += f'\n✓ Auto-created loan account: {loan_account_name}'
                    else:
                        success_msg += '\n(No recurring payment created - missing payment account)'
                    
                    QMessageBox.information(self, 'Loan Added', success_msg)
                
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to add loan: {e}')

    def process_loans(self):
        """Process all due loan payments."""
        try:
            count = self.bank.process_loan_payments()
            QMessageBox.information(self, 'Loans', f'Processed {count} loan payment(s).')
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to process loans: {e}')

    def remove_loan(self, loan_identifier):
        """Remove a loan by identifier after confirmation."""
        reply = QMessageBox.question(self, 'Confirm Delete', 'Delete this loan?')
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.bank.remove_loan(loan_identifier)
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to remove loan: {e}')
    
    def view_loan_details(self, loan):
        """Open loan details dialog with amortization schedule"""
        try:
            dialog = LoanDetailsDialog(loan, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open loan details: {e}')
            print(f"[ERROR] view_loan_details: {e}")
            import traceback
            traceback.print_exc()

    # Budget Management Methods
    
    def add_budget(self):
        """Show dialog to add a new budget"""
        dialog = AddBudgetDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                budget = Budget(
                    category=data['category'],
                    monthly_limit=data['monthly_limit'],
                    user_id=self.current_user_id,
                    notes=data.get('notes', ''),
                    warning_threshold=data.get('warning_threshold', 0.8)
                )
                self.budget_manager.add_budget(budget)
                QMessageBox.information(self, 'Budget Added', f'Budget for "{data["category"]}" added successfully!')
                self.update_budget_table()
                self.update_transactions_table()  # Refresh to show budget colors
            except Exception as e:
                print(f"[ERROR] Error adding budget: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, 'Error', f'Failed to add budget: {e}')
    
    def update_budget_table(self):
        """Update the budgets table with current data"""
        try:
            # Get selected month
            selected_date = self.budget_month_selector.date().toPyDate()
            year = selected_date.year
            month = selected_date.month
            
            # Get all transactions for budget calculation
            transactions = self.bank.list_transactions(user_id=self.current_user_id)
            
            # Get budget summary
            summary = self.budget_manager.get_monthly_summary(transactions, year, month)
            
            # Update summary label
            remaining = summary['total_budgeted'] - summary['total_spent']
            self.budget_summary_label.setText(
                f"Total Budgeted: ${summary['total_budgeted']:,.2f} | "
                f"Total Spent: ${summary['total_spent']:,.2f} | "
                f"Remaining: ${remaining:,.2f}"
            )
            
            # Set summary label color
            if remaining < 0:
                self.budget_summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #F44336;")
            elif remaining < summary['total_budgeted'] * 0.2:
                self.budget_summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")
            else:
                self.budget_summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
            
            # Update table
            budgets = self.budget_manager.get_all_budgets()
            self.budgets_table.setRowCount(len(budgets))
            
            for row, budget in enumerate(budgets):
                status = self.budget_manager.get_budget_status(transactions, budget.category, year, month)
                
                # Category
                category_item = QTableWidgetItem(budget.category)
                self.budgets_table.setItem(row, 0, category_item)
                
                # Monthly Limit
                limit_item = QTableWidgetItem(f'${budget.monthly_limit:,.2f}')
                self.budgets_table.setItem(row, 1, limit_item)
                
                # Spent
                spent_item = QTableWidgetItem(f'${status["spent"]:,.2f}')
                spent_item.setBackground(QBrush(QColor(status['color'])))
                self.budgets_table.setItem(row, 2, spent_item)
                
                # Remaining
                remaining_item = QTableWidgetItem(f'${status["remaining"]:,.2f}')
                remaining_item.setBackground(QBrush(QColor(status['color'])))
                self.budgets_table.setItem(row, 3, remaining_item)
                
                # Progress %
                progress_pct = status['percentage'] * 100
                progress_item = QTableWidgetItem(f'{progress_pct:.1f}%')
                progress_item.setBackground(QBrush(QColor(status['color'])))
                self.budgets_table.setItem(row, 4, progress_item)
                
                # Status
                status_text = status['status'].replace('_', ' ').title()
                status_item = QTableWidgetItem(status_text)
                status_item.setBackground(QBrush(QColor(status['color'])))
                if status['status'] == 'good':
                    status_item.setForeground(QBrush(QColor('white')))
                self.budgets_table.setItem(row, 5, status_item)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(2, 2, 2, 2)
                
                edit_btn = QPushButton('Edit')
                edit_btn.clicked.connect(lambda checked, b=budget: self.edit_budget(b))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton('Delete')
                delete_btn.clicked.connect(lambda checked, b=budget: self.delete_budget(b))
                actions_layout.addWidget(delete_btn)
                
                actions_widget.setLayout(actions_layout)
                self.budgets_table.setCellWidget(row, 6, actions_widget)
                
        except Exception as e:
            print(f"[ERROR] Error updating budget table: {e}")
            import traceback
            traceback.print_exc()
    
    def edit_budget(self, budget):
        """Edit an existing budget"""
        dialog = AddBudgetDialog(self, budget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                self.budget_manager.update_budget(
                    budget.identifier,
                    category=data['category'],
                    monthly_limit=data['monthly_limit'],
                    notes=data.get('notes', ''),
                    warning_threshold=data.get('warning_threshold', 0.8)
                )
                QMessageBox.information(self, 'Budget Updated', 'Budget updated successfully!')
                self.update_budget_table()
                self.update_transactions_table()  # Refresh to show updated budget colors
            except Exception as e:
                print(f"[ERROR] Error updating budget: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, 'Error', f'Failed to update budget: {e}')
    
    def delete_budget(self, budget):
        """Delete a budget"""
        reply = QMessageBox.question(
            self, 'Confirm Delete',
            f'Are you sure you want to delete the budget for "{budget.category}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.budget_manager.remove_budget(budget.identifier)
                QMessageBox.information(self, 'Budget Deleted', 'Budget deleted successfully!')
                self.update_budget_table()
                self.update_transactions_table()  # Refresh to remove budget colors
            except Exception as e:
                print(f"[ERROR] Error deleting budget: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, 'Error', f'Failed to delete budget: {e}')
    
    def add_goal(self):
        """Open dialog to add a new goal"""
        dialog = AddGoalDialog(self, self.goal_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.goal_manager.add_goal(
                name=data['name'],
                target_amount=data['target_amount'],
                target_date=data.get('target_date'),
                monthly_contribution=data.get('monthly_contribution', 0.0),
                linked_account_id=data.get('linked_account_id'),
                priority=data.get('priority', 'medium'),
                icon=data.get('icon', '💰'),
                notes=data.get('notes', ''),
                user_id=self.current_user_id
            )
            self.update_goals_display()
            QMessageBox.information(self, 'Success', f'Goal "{data["name"]}" created!')
    
    def edit_goal(self, goal_id):
        """Open dialog to edit a goal"""
        goal = self.goal_manager.get_goal(goal_id)
        if not goal:
            return
        
        dialog = AddGoalDialog(self, self.goal_manager, goal=goal)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.goal_manager.update_goal(
                goal_id,
                name=data['name'],
                target_amount=data['target_amount'],
                target_date=data.get('target_date'),
                monthly_contribution=data.get('monthly_contribution', 0.0),
                linked_account_id=data.get('linked_account_id'),
                priority=data.get('priority', 'medium'),
                icon=data.get('icon', '💰'),
                notes=data.get('notes', '')
            )
            self.update_goals_display()
            QMessageBox.information(self, 'Success', 'Goal updated!')
    
    def delete_goal(self, goal_id):
        """Delete a goal with confirmation"""
        goal = self.goal_manager.get_goal(goal_id)
        if not goal:
            return
        
        reply = QMessageBox.question(
            self,
            'Delete Goal',
            f'Delete goal "{goal.name}"?\n\nThis will remove all contribution history.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.goal_manager.remove_goal(goal_id)
            self.update_goals_display()
            QMessageBox.information(self, 'Deleted', f'Goal "{goal.name}" deleted.')
    
    def contribute_to_goal(self, goal_id):
        """Open dialog to contribute to a goal"""
        goal = self.goal_manager.get_goal(goal_id)
        if not goal:
            return
        
        dialog = ContributeToGoalDialog(self, goal)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            amount = dialog.get_amount()
            self.goal_manager.add_contribution_to_goal(goal_id, amount)
            self.update_goals_display()
            
            # Check if goal was just completed
            goal = self.goal_manager.get_goal(goal_id)
            if goal.completed and goal.completed_date == date.today().isoformat():
                QMessageBox.information(
                    self,
                    '🎉 Goal Achieved!',
                    f'Congratulations! You\'ve reached your "{goal.name}" goal!\n\n'
                    f'Target: ${goal.target_amount:,.2f}\n'
                    f'Achieved: ${goal.current_amount:,.2f}\n\n'
                    f'Keep up the great work! 🎊'
                )
    
    def show_goal_statistics(self):
        """Show goal statistics dialog"""
        dialog = GoalStatisticsDialog(self, self.goal_manager, self.current_user_id)
        dialog.exec()
    
    def update_goals_display(self):
        """Update the goals display with cards for each goal"""
        # Clear existing cards
        while self.goals_layout.count():
            item = self.goals_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get goals for current user
        goals = self.goal_manager.list_goals(user_id=self.current_user_id, completed=False)
        
        if not goals:
            # Show empty state
            empty_label = QLabel('No goals yet. Click "➕ Add Goal" to get started!')
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet('color: #999; font-size: 14px; padding: 40px;')
            self.goals_layout.addWidget(empty_label)
        else:
            # Create card for each goal
            for goal in goals:
                card = self.create_goal_card(goal)
                self.goals_layout.addWidget(card)
        
        # Add completed goals section if any
        completed_goals = self.goal_manager.list_goals(user_id=self.current_user_id, completed=True)
        if completed_goals:
            completed_header = QLabel('🎉 Completed Goals')
            completed_header.setFont(QFont('Arial', 12, QFont.Weight.Bold))
            completed_header.setStyleSheet('color: #4CAF50; margin-top: 20px;')
            self.goals_layout.addWidget(completed_header)
            
            for goal in completed_goals[:3]:  # Show last 3 completed
                card = self.create_goal_card(goal, completed=True)
                self.goals_layout.addWidget(card)
        
        self.goals_layout.addStretch()
    
    def create_goal_card(self, goal, completed=False):
        """Create a visual card for a goal with progress bar"""
        card = QGroupBox()
        card.setStyleSheet('''
            QGroupBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
        ''' if not completed else '''
            QGroupBox {
                background-color: #f0f8f0;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
                opacity: 0.8;
            }
        ''')
        
        layout = QVBoxLayout()
        
        # Header: Icon + Name + Priority
        header_layout = QHBoxLayout()
        
        icon_label = QLabel(goal.icon)
        icon_label.setFont(QFont('Arial', 24))
        header_layout.addWidget(icon_label)
        
        name_label = QLabel(goal.name)
        name_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # Priority badge
        priority_colors = {
            'critical': '#f44336',
            'high': '#ff9800',
            'medium': '#2196F3',
            'low': '#9e9e9e'
        }
        priority_label = QLabel(goal.priority.upper())
        priority_label.setStyleSheet(f'''
            background-color: {priority_colors.get(goal.priority, '#9e9e9e')};
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 10px;
        ''')
        header_layout.addWidget(priority_label)
        
        layout.addLayout(header_layout)
        
        # Progress info
        progress_pct = goal.get_progress_percentage()
        progress_label = QLabel(f'${goal.current_amount:,.2f} / ${goal.target_amount:,.2f}  ({progress_pct:.1f}%)')
        progress_label.setFont(QFont('Arial', 12))
        layout.addWidget(progress_label)
        
        # Progress bar
        from PyQt6.QtWidgets import QProgressBar
        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(int(progress_pct))
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet(f'''
            QProgressBar {{
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f5f5f5;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {'#4CAF50' if completed else '#2196F3'};
                border-radius: 3px;
            }}
        ''')
        layout.addWidget(progress_bar)
        
        # Details row
        details_layout = QGridLayout()
        details_layout.setSpacing(10)
        
        col = 0
        
        # Remaining amount
        remaining_label = QLabel(f'<b>Remaining:</b> ${goal.get_remaining_amount():,.2f}')
        remaining_label.setStyleSheet('font-size: 11px;')
        details_layout.addWidget(remaining_label, 0, col)
        col += 1
        
        # Target date
        if goal.target_date:
            days_left = goal.get_days_until_target()
            if days_left is not None:
                if days_left > 0:
                    date_text = f'<b>Target:</b> {goal.target_date} ({days_left} days)'
                elif days_left == 0:
                    date_text = f'<b>Target:</b> Today!'
                else:
                    date_text = f'<b>Target:</b> Overdue by {abs(days_left)} days'
                
                date_label = QLabel(date_text)
                date_label.setStyleSheet('font-size: 11px;' if days_left >= 0 else 'font-size: 11px; color: #f44336;')
                details_layout.addWidget(date_label, 0, col)
                col += 1
        
        # Monthly contribution
        if goal.monthly_contribution > 0:
            contrib_label = QLabel(f'<b>Monthly:</b> ${goal.monthly_contribution:,.2f}')
            contrib_label.setStyleSheet('font-size: 11px;')
            details_layout.addWidget(contrib_label, 0, col)
            col += 1
        
        layout.addLayout(details_layout)
        
        # Projection row
        projection_layout = QHBoxLayout()
        
        if not completed:
            # Show projection
            if goal.monthly_contribution > 0:
                projected_date = goal.get_projected_completion_date()
                if projected_date:
                    status = goal.is_on_track()
                    status_icons = {'ahead': '🚀', 'on-track': '✅', 'behind': '⚠️'}
                    status_colors = {'ahead': '#4CAF50', 'on-track': '#2196F3', 'behind': '#ff9800'}
                    
                    proj_text = f'{status_icons.get(status, "📅")} Projected: {projected_date}'
                    proj_label = QLabel(proj_text)
                    proj_label.setStyleSheet(f'font-size: 11px; color: {status_colors.get(status, "#666")};')
                    projection_layout.addWidget(proj_label)
            
            # Required monthly contribution
            if goal.target_date:
                required = goal.get_required_monthly_contribution()
                if required and required > 0:
                    req_label = QLabel(f'Need ${required:,.2f}/month to reach goal on time')
                    req_label.setStyleSheet('font-size: 11px; color: #666; font-style: italic;')
                    projection_layout.addWidget(req_label)
        else:
            completed_label = QLabel(f'✅ Completed on {goal.completed_date}!')
            completed_label.setStyleSheet('font-size: 12px; color: #4CAF50; font-weight: bold;')
            projection_layout.addWidget(completed_label)
        
        projection_layout.addStretch()
        layout.addLayout(projection_layout)
        
        # Action buttons
        if not completed:
            buttons_layout = QHBoxLayout()
            
            contribute_btn = QPushButton('💰 Contribute')
            contribute_btn.clicked.connect(lambda: self.contribute_to_goal(goal.goal_id))
            contribute_btn.setStyleSheet('padding: 6px 12px; background-color: #4CAF50; color: white; font-weight: bold;')
            buttons_layout.addWidget(contribute_btn)
            
            edit_btn = QPushButton('✏️ Edit')
            edit_btn.clicked.connect(lambda: self.edit_goal(goal.goal_id))
            buttons_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton('🗑️ Delete')
            delete_btn.clicked.connect(lambda: self.delete_goal(goal.goal_id))
            delete_btn.setStyleSheet('color: #f44336;')
            buttons_layout.addWidget(delete_btn)
            
            buttons_layout.addStretch()
            layout.addLayout(buttons_layout)
        
        card.setLayout(layout)
        return card
    
    def update_net_worth_display(self):
        """Update the net worth display with current data and trends"""
        from PyQt6.QtWidgets import QProgressBar, QScrollArea
        
        # Clear existing widgets
        while self.net_worth_layout.count():
            item = self.net_worth_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Calculate current net worth
        current_snapshot = self.net_worth_tracker.calculate_current_net_worth(
            self.bank, self.bank.account_manager, self.current_user_id
        )
        
        # Current Net Worth Card
        current_card = self.create_net_worth_current_card(current_snapshot)
        self.net_worth_layout.addWidget(current_card)
        
        # Growth Statistics Card
        growth_card = self.create_net_worth_growth_card()
        self.net_worth_layout.addWidget(growth_card)
        
        # Trend Chart
        chart_card = self.create_net_worth_chart()
        self.net_worth_layout.addWidget(chart_card)
        
        # Asset/Liability Breakdown
        breakdown_card = self.create_net_worth_breakdown(current_snapshot)
        self.net_worth_layout.addWidget(breakdown_card)
        
        self.net_worth_layout.addStretch()
    
    def create_net_worth_current_card(self, snapshot):
        """Create card showing current net worth snapshot"""
        card = QGroupBox('💰 Current Net Worth')
        card.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        
        # Net Worth amount (large)
        net_worth_label = QLabel(f'${snapshot.net_worth:,.2f}')
        net_worth_label.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        net_worth_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Color code based on positive/negative
        if snapshot.net_worth >= 0:
            net_worth_label.setStyleSheet('color: #2e7d32;')  # Green
        else:
            net_worth_label.setStyleSheet('color: #c62828;')  # Red
        
        layout.addWidget(net_worth_label)
        
        # Date
        date_label = QLabel(f'As of {snapshot.date}')
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_label.setStyleSheet('color: #666; font-style: italic;')
        layout.addWidget(date_label)
        
        # Assets and Liabilities breakdown
        breakdown_layout = QHBoxLayout()
        
        # Assets
        assets_group = QVBoxLayout()
        assets_label = QLabel('Assets')
        assets_label.setStyleSheet('font-weight: bold; color: #2e7d32;')
        assets_amount = QLabel(f'${snapshot.assets:,.2f}')
        assets_amount.setStyleSheet('font-size: 16pt; color: #2e7d32;')
        assets_group.addWidget(assets_label)
        assets_group.addWidget(assets_amount)
        breakdown_layout.addLayout(assets_group)
        
        breakdown_layout.addStretch()
        
        # Liabilities
        liabilities_group = QVBoxLayout()
        liabilities_label = QLabel('Liabilities')
        liabilities_label.setStyleSheet('font-weight: bold; color: #c62828;')
        liabilities_amount = QLabel(f'${snapshot.liabilities:,.2f}')
        liabilities_amount.setStyleSheet('font-size: 16pt; color: #c62828;')
        liabilities_group.addWidget(liabilities_label)
        liabilities_group.addWidget(liabilities_amount)
        breakdown_layout.addLayout(liabilities_group)
        
        layout.addLayout(breakdown_layout)
        
        card.setLayout(layout)
        card.setStyleSheet('''
            QGroupBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        ''')
        
        return card
    
    def create_net_worth_growth_card(self):
        """Create card showing growth statistics"""
        card = QGroupBox('📈 Growth Statistics')
        card.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        
        # Get growth data for different periods
        periods = [
            ('1 Month', 1),
            ('3 Months', 3),
            ('6 Months', 6),
            ('1 Year', 12)
        ]
        
        grid = QGridLayout()
        row = 0
        
        for period_name, months in periods:
            growth = self.net_worth_tracker.get_growth_rate(self.current_user_id, months)
            
            # Period label
            period_label = QLabel(period_name)
            period_label.setStyleSheet('font-weight: bold;')
            grid.addWidget(period_label, row, 0)
            
            if growth['insufficient_data']:
                value_label = QLabel('N/A')
                value_label.setStyleSheet('color: #999;')
            else:
                # Absolute change
                abs_change = growth['absolute_change']
                pct_change = growth['percentage_change']
                
                # Format with + or -
                sign = '+' if abs_change >= 0 else ''
                value_text = f'{sign}${abs_change:,.2f} ({sign}{pct_change:.1f}%)'
                
                value_label = QLabel(value_text)
                
                # Color code
                if abs_change >= 0:
                    value_label.setStyleSheet('color: #2e7d32; font-weight: bold;')
                else:
                    value_label.setStyleSheet('color: #c62828; font-weight: bold;')
            
            grid.addWidget(value_label, row, 1)
            row += 1
        
        layout.addLayout(grid)
        
        # Monthly average
        growth_12mo = self.net_worth_tracker.get_growth_rate(self.current_user_id, 12)
        if not growth_12mo['insufficient_data']:
            monthly_avg = growth_12mo['monthly_average']
            avg_label = QLabel(f'\nAverage Monthly Change: ${monthly_avg:,.2f}')
            avg_label.setStyleSheet('font-style: italic; color: #666;')
            layout.addWidget(avg_label)
        
        card.setLayout(layout)
        card.setStyleSheet('''
            QGroupBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        ''')
        
        return card
    
    def create_net_worth_chart(self):
        """Create card with net worth trend chart"""
        card = QGroupBox('📊 Net Worth Trend')
        card.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        card.setMinimumHeight(750)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Get historical snapshots
        snapshots = self.net_worth_tracker.get_snapshots_for_user(self.current_user_id)
        
        if len(snapshots) < 2:
            # Not enough data
            no_data_label = QLabel('📉 Not enough historical data to show trend.\nTake snapshots over time to see your progress!')
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_label.setStyleSheet('color: #999; font-style: italic; padding: 40px;')
            layout.addWidget(no_data_label)
        else:
            # Create matplotlib chart with larger size
            figure = Figure(figsize=(16, 8), dpi=100)
            canvas = FigureCanvas(figure)
            
            # Set explicit sizing for canvas
            canvas.setMinimumHeight(550)
            from PyQt6.QtWidgets import QSizePolicy
            size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            size_policy.setHeightForWidth(True)
            canvas.setSizePolicy(size_policy)
            
            ax = figure.add_subplot(111)
            
            # Extract dates and values
            dates = [datetime.strptime(s.date, '%Y-%m-%d') for s in snapshots]
            net_worths = [s.net_worth for s in snapshots]
            assets = [s.assets for s in snapshots]
            liabilities = [s.liabilities for s in snapshots]
            
            # Plot lines
            ax.plot(dates, net_worths, marker='o', linewidth=3.5, markersize=12, color='#1976d2', label='Net Worth')
            ax.plot(dates, assets, marker='s', linewidth=2.5, markersize=8, color='#2e7d32', linestyle='--', label='Assets')
            ax.plot(dates, liabilities, marker='^', linewidth=2.5, markersize=8, color='#c62828', linestyle='--', label='Liabilities')
            
            # Zero line
            ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3, linewidth=1)
            
            # Labels and formatting
            ax.set_xlabel('Date', fontsize=13, fontweight='bold')
            ax.set_ylabel('Amount ($)', fontsize=13, fontweight='bold')
            ax.set_title('Net Worth Over Time', fontsize=15, fontweight='bold', pad=25)
            ax.legend(loc='upper left', fontsize=12, framealpha=0.98, edgecolor='black')
            ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.8)
            
            # Format y-axis as currency
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            # Rotate date labels
            figure.autofmt_xdate(rotation=45, ha='right')
            
            # Add padding around the chart - give more room at top for title
            figure.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.13)
            
            layout.addWidget(canvas)
        
        card.setLayout(layout)
        card.setStyleSheet('''
            QGroupBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        ''')
        
        return card
    
    def create_net_worth_breakdown(self, snapshot):
        """Create card with detailed account breakdown"""
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
        
        card = QGroupBox('📋 Account Breakdown')
        card.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        
        # Create table
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(['Account', 'Balance', 'Type'])
        table.horizontalHeader().setStretchLastSection(True)
        
        # Add accounts
        breakdown = snapshot.account_breakdown
        row = 0
        
        for account_name, balance in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
            table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(account_name)
            table.setItem(row, 0, name_item)
            
            # Balance
            balance_item = QTableWidgetItem(f'${abs(balance):,.2f}')
            balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Color code
            if balance >= 0:
                balance_item.setForeground(QBrush(QColor('#2e7d32')))
            else:
                balance_item.setForeground(QBrush(QColor('#c62828')))
            
            table.setItem(row, 1, balance_item)
            
            # Type
            type_text = 'Asset' if balance >= 0 else 'Liability'
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 2, type_item)
            
            row += 1
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        card.setLayout(layout)
        card.setStyleSheet('''
            QGroupBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        ''')
        
        return card
    
    def take_net_worth_snapshot(self):
        """Manually take a net worth snapshot"""
        try:
            # Calculate current net worth
            snapshot = self.net_worth_tracker.calculate_current_net_worth(
                self.bank, self.bank.account_manager, self.current_user_id
            )
            
            # Save snapshot
            self.net_worth_tracker.add_snapshot(snapshot)
            
            QMessageBox.information(
                self,
                'Snapshot Saved',
                f'Net worth snapshot saved!\n\nNet Worth: ${snapshot.net_worth:,.2f}\nAssets: ${snapshot.assets:,.2f}\nLiabilities: ${snapshot.liabilities:,.2f}'
            )
            
            # Refresh display
            self.update_net_worth_display()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to take snapshot: {e}')
    
    def view_net_worth_history(self):
        """Show dialog with net worth history"""
        dialog = NetWorthHistoryDialog(self.net_worth_tracker, self.current_user_id, self)
        dialog.exec()
    
    def export_net_worth(self):
        """Export net worth history to CSV"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Export Net Worth History',
            'net_worth_history.csv',
            'CSV Files (*.csv)'
        )
        
        if file_path:
            success = self.net_worth_tracker.export_to_csv(file_path, self.current_user_id)
            if success:
                QMessageBox.information(self, 'Export Successful', f'Net worth history exported to:\n{file_path}')
            else:
                QMessageBox.warning(self, 'Export Failed', 'Failed to export net worth history.')


class AttachmentViewerDialog(QDialog):
    """Dialog for viewing transaction attachments (images and PDFs)"""
    
    def __init__(self, parent=None, attachments=None, current_index=0, attachment_manager=None):
        super().__init__(parent)
        self.attachments = attachments or []
        self.current_index = current_index
        self.attachment_manager = attachment_manager
        
        self.setWindowTitle('View Attachments')
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Navigation bar
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton('← Previous')
        self.prev_btn.clicked.connect(self.show_previous)
        nav_layout.addWidget(self.prev_btn)
        
        self.file_info_label = QLabel()
        self.file_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.file_info_label, 1)
        
        self.next_btn = QPushButton('Next →')
        self.next_btn.clicked.connect(self.show_next)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # Content area
        self.content_label = QLabel()
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setStyleSheet('background-color: #f0f0f0; border: 1px solid #ccc;')
        self.content_label.setMinimumSize(600, 400)
        layout.addWidget(self.content_label, 1)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.open_btn = QPushButton('Open in System Viewer')
        self.open_btn.clicked.connect(self.open_in_system_viewer)
        button_layout.addWidget(self.open_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Show first attachment
        self.show_current_attachment()
    
    def show_current_attachment(self):
        """Display the current attachment"""
        if not self.attachments or self.current_index >= len(self.attachments):
            self.content_label.setText('No attachment to display')
            self.file_info_label.setText('')
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.open_btn.setEnabled(False)
            return
        
        attachment = self.attachments[self.current_index]
        filename = attachment.get('filename', 'Unknown')
        file_type = attachment.get('type', '')
        file_size = attachment.get('size', 0)
        
        # Format file info
        if self.attachment_manager:
            size_str = self.attachment_manager.format_file_size(file_size)
        else:
            size_str = f"{file_size} bytes"
        
        info_text = f"{filename} ({size_str}) - {self.current_index + 1}/{len(self.attachments)}"
        self.file_info_label.setText(info_text)
        
        # Get file path
        if self.attachment_manager:
            file_path = self.attachment_manager.get_attachment_path(attachment)
        else:
            file_path = attachment.get('path')
        
        if not file_path or not os.path.exists(file_path):
            self.content_label.setText(f'❌ File not found:\n{filename}')
            self.open_btn.setEnabled(False)
            self.update_navigation_buttons()
            return
        
        self.open_btn.setEnabled(True)
        
        # Display based on file type
        if file_type.startswith('image/'):
            self.display_image(file_path)
        elif file_type == 'application/pdf':
            self.display_pdf_placeholder(filename)
        else:
            # Show file icon for other types
            if self.attachment_manager:
                icon = self.attachment_manager.get_file_icon(file_type)
            else:
                icon = '📄'
            self.content_label.setText(f'{icon}\n\n{filename}\n\nClick "Open in System Viewer" to view this file')
        
        self.update_navigation_buttons()
    
    def display_image(self, image_path):
        """Display an image in the content area"""
        from PyQt6.QtGui import QPixmap
        
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.content_label.setText(f'❌ Failed to load image')
            return
        
        # Scale image to fit while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.content_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.content_label.setPixmap(scaled_pixmap)
    
    def display_pdf_placeholder(self, filename):
        """Display placeholder for PDF (PDFs require external viewer)"""
        self.content_label.setText(f'📕 PDF Document\n\n{filename}\n\nClick "Open in System Viewer" to view this PDF')
    
    def show_previous(self):
        """Show previous attachment"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_attachment()
    
    def show_next(self):
        """Show next attachment"""
        if self.current_index < len(self.attachments) - 1:
            self.current_index += 1
            self.show_current_attachment()
    
    def update_navigation_buttons(self):
        """Update navigation button states"""
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.attachments) - 1)
    
    def open_in_system_viewer(self):
        """Open the current attachment in the system's default viewer"""
        if not self.attachments or self.current_index >= len(self.attachments):
            return
        
        attachment = self.attachments[self.current_index]
        
        # Get file path
        if self.attachment_manager:
            file_path = self.attachment_manager.get_attachment_path(attachment)
        else:
            file_path = attachment.get('path')
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, 'File Not Found', 'The attachment file could not be found')
            return
        
        # Open in system viewer
        import subprocess
        import platform
        
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open file:\n{e}')


class SplitTransactionDialog(QDialog):
    """Dialog for creating/editing transaction splits"""
    
    def __init__(self, parent=None, total_amount=0.0, existing_splits=None, categories=None):
        super().__init__(parent)
        self.total_amount = total_amount
        self.splits = existing_splits.copy() if existing_splits else []
        self.categories = categories or []
        
        self.setWindowTitle('Split Transaction')
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(f'Total Transaction Amount: ${self.total_amount:.2f}\nSplit this transaction across multiple categories:')
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Splits table
        self.splits_table = QTableWidget()
        self.splits_table.setColumnCount(3)
        self.splits_table.setHorizontalHeaderLabels(['Category', 'Amount', 'Actions'])
        self.splits_table.horizontalHeader().setStretchLastSection(False)
        self.splits_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.splits_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.splits_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.splits_table.setColumnWidth(1, 120)
        self.splits_table.setColumnWidth(2, 80)
        layout.addWidget(self.splits_table)
        
        # Load existing splits
        self.refresh_splits_table()
        
        # Add split button
        add_btn = QPushButton('Add Split')
        add_btn.clicked.connect(self.add_split_row)
        layout.addWidget(add_btn)
        
        # Summary section
        summary_layout = QHBoxLayout()
        self.splits_total_label = QLabel('Splits Total: $0.00')
        self.remaining_label = QLabel(f'Remaining: ${self.total_amount:.2f}')
        self.validation_label = QLabel('')
        self.validation_label.setStyleSheet('color: red; font-weight: bold;')
        
        summary_layout.addWidget(self.splits_total_label)
        summary_layout.addWidget(self.remaining_label)
        summary_layout.addWidget(self.validation_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Update summary on startup
        self.update_summary()
    
    def refresh_splits_table(self):
        """Refresh the splits table with current splits data"""
        self.splits_table.setRowCount(len(self.splits))
        
        for row, split in enumerate(self.splits):
            # Category combo box
            category_combo = QComboBox()
            category_combo.setEditable(True)
            category_combo.addItems(self.categories)
            category_combo.setCurrentText(split['category'])
            category_combo.currentTextChanged.connect(lambda text, r=row: self.on_split_changed(r))
            self.splits_table.setCellWidget(row, 0, category_combo)
            
            # Amount spin box
            amount_spin = QDoubleSpinBox()
            amount_spin.setPrefix('$')
            amount_spin.setMaximum(self.total_amount)
            amount_spin.setDecimals(2)
            amount_spin.setValue(split['amount'])
            amount_spin.valueChanged.connect(lambda val, r=row: self.on_split_changed(r))
            self.splits_table.setCellWidget(row, 1, amount_spin)
            
            # Delete button
            delete_btn = QPushButton('Delete')
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_split_row(r))
            self.splits_table.setCellWidget(row, 2, delete_btn)
    
    def add_split_row(self):
        """Add a new split row"""
        remaining = self.total_amount - sum(s['amount'] for s in self.splits)
        self.splits.append({'category': '', 'amount': max(0, remaining)})
        self.refresh_splits_table()
        self.update_summary()
    
    def delete_split_row(self, row):
        """Delete a split row"""
        if 0 <= row < len(self.splits):
            self.splits.pop(row)
            self.refresh_splits_table()
            self.update_summary()
    
    def on_split_changed(self, row):
        """Handle changes to split data"""
        if 0 <= row < len(self.splits):
            # Get category from combo box
            category_combo = self.splits_table.cellWidget(row, 0)
            if category_combo:
                self.splits[row]['category'] = category_combo.currentText()
            
            # Get amount from spin box
            amount_spin = self.splits_table.cellWidget(row, 1)
            if amount_spin:
                self.splits[row]['amount'] = amount_spin.value()
            
            self.update_summary()
    
    def update_summary(self):
        """Update the summary labels showing totals and remaining amount"""
        splits_total = sum(s['amount'] for s in self.splits)
        remaining = self.total_amount - splits_total
        
        self.splits_total_label.setText(f'Splits Total: ${splits_total:.2f}')
        self.remaining_label.setText(f'Remaining: ${remaining:.2f}')
        
        # Validation feedback
        if abs(remaining) < 0.01:
            self.validation_label.setText('✓ Valid')
            self.validation_label.setStyleSheet('color: green; font-weight: bold;')
        elif remaining > 0:
            self.validation_label.setText(f'⚠ Under by ${remaining:.2f}')
            self.validation_label.setStyleSheet('color: orange; font-weight: bold;')
        else:
            self.validation_label.setText(f'✗ Over by ${abs(remaining):.2f}')
            self.validation_label.setStyleSheet('color: red; font-weight: bold;')
    
    def validate_and_accept(self):
        """Validate splits before accepting"""
        # Remove empty splits
        self.splits = [s for s in self.splits if s['category'].strip() and s['amount'] > 0]
        
        # Check if splits sum to total
        splits_total = sum(s['amount'] for s in self.splits)
        if abs(splits_total - self.total_amount) >= 0.01:
            QMessageBox.warning(
                self,
                'Invalid Splits',
                f'Splits total (${splits_total:.2f}) must equal transaction amount (${self.total_amount:.2f})'
            )
            return
        
        # Check for empty categories
        if any(not s['category'].strip() for s in self.splits):
            QMessageBox.warning(self, 'Invalid Splits', 'All splits must have a category')
            return
        
        self.accept()
    
    def get_splits(self):
        """Get the current splits data"""
        return self.splits


class RuleManagerDialog(QDialog):
    """Dialog for managing transaction categorization rules"""
    
    def __init__(self, parent=None, rule_manager=None):
        super().__init__(parent)
        self.rule_manager = rule_manager
        
        self.setWindowTitle('Transaction Rules Manager')
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel('Automatically categorize transactions based on description patterns')
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(7)
        self.rules_table.setHorizontalHeaderLabels([
            'Priority', 'Pattern', 'Match Type', 'Category', 'Type', 'Enabled', 'Actions'
        ])
        self.rules_table.horizontalHeader().setStretchLastSection(False)
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.rules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.rules_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.rules_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.rules_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.rules_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.rules_table.setColumnWidth(0, 60)
        self.rules_table.setColumnWidth(2, 100)
        self.rules_table.setColumnWidth(3, 120)
        self.rules_table.setColumnWidth(4, 80)
        self.rules_table.setColumnWidth(5, 70)
        self.rules_table.setColumnWidth(6, 180)
        layout.addWidget(self.rules_table)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton('➕ Add Rule')
        add_btn.clicked.connect(self.add_rule)
        buttons_layout.addWidget(add_btn)
        
        test_btn = QPushButton('🧪 Test Rule')
        test_btn.clicked.connect(self.test_rule)
        buttons_layout.addWidget(test_btn)
        
        apply_btn = QPushButton('📋 Apply to All Transactions')
        apply_btn.clicked.connect(self.apply_to_all)
        buttons_layout.addWidget(apply_btn)
        
        buttons_layout.addStretch()
        
        stats_btn = QPushButton('📊 Statistics')
        stats_btn.clicked.connect(self.show_statistics)
        buttons_layout.addWidget(stats_btn)
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Load rules
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the rules table"""
        if not self.rule_manager:
            return
        
        rules = self.rule_manager.list_rules()
        self.rules_table.setRowCount(len(rules))
        
        for row, rule in enumerate(rules):
            # Priority
            priority_item = QTableWidgetItem(str(rule.priority + 1))
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.rules_table.setItem(row, 0, priority_item)
            
            # Pattern
            pattern_item = QTableWidgetItem(rule.pattern)
            if rule.notes:
                pattern_item.setToolTip(rule.notes)
            self.rules_table.setItem(row, 1, pattern_item)
            
            # Match Type
            match_type_item = QTableWidgetItem(rule.match_type.title())
            match_type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.rules_table.setItem(row, 2, match_type_item)
            
            # Category
            category_item = QTableWidgetItem(rule.category)
            self.rules_table.setItem(row, 3, category_item)
            
            # Type
            type_text = rule.type if rule.type else 'Any'
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.rules_table.setItem(row, 4, type_item)
            
            # Enabled checkbox
            enabled_widget = QWidget()
            enabled_layout = QHBoxLayout(enabled_widget)
            enabled_layout.setContentsMargins(0, 0, 0, 0)
            enabled_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            enabled_check = QCheckBox()
            enabled_check.setChecked(rule.enabled)
            enabled_check.stateChanged.connect(lambda state, r=rule: self.toggle_rule(r, state))
            enabled_layout.addWidget(enabled_check)
            
            self.rules_table.setCellWidget(row, 5, enabled_widget)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 0, 4, 0)
            
            edit_btn = QPushButton('Edit')
            edit_btn.clicked.connect(lambda checked, r=rule: self.edit_rule(r))
            actions_layout.addWidget(edit_btn)
            
            up_btn = QPushButton('↑')
            up_btn.setMaximumWidth(30)
            up_btn.setEnabled(row > 0)
            up_btn.clicked.connect(lambda checked, r=row: self.move_rule_up(r))
            actions_layout.addWidget(up_btn)
            
            down_btn = QPushButton('↓')
            down_btn.setMaximumWidth(30)
            down_btn.setEnabled(row < len(rules) - 1)
            down_btn.clicked.connect(lambda checked, r=row: self.move_rule_down(r))
            actions_layout.addWidget(down_btn)
            
            delete_btn = QPushButton('Delete')
            delete_btn.clicked.connect(lambda checked, r=rule: self.delete_rule(r))
            actions_layout.addWidget(delete_btn)
            
            self.rules_table.setCellWidget(row, 6, actions_widget)
    
    def add_rule(self):
        """Open dialog to add a new rule"""
        dialog = AddRuleDialog(self, self.rule_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
    
    def edit_rule(self, rule):
        """Open dialog to edit a rule"""
        dialog = AddRuleDialog(self, self.rule_manager, rule)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
    
    def delete_rule(self, rule):
        """Delete a rule"""
        reply = QMessageBox.question(
            self,
            'Confirm Delete',
            f'Delete rule "{rule.pattern}" → {rule.category}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.rule_manager.remove_rule(rule.identifier)
            self.refresh_table()
    
    def toggle_rule(self, rule, state):
        """Toggle rule enabled status"""
        enabled = (state == Qt.CheckState.Checked.value)
        self.rule_manager.update_rule(rule.identifier, enabled=enabled)
    
    def move_rule_up(self, row):
        """Move rule up in priority"""
        rules = self.rule_manager.list_rules()
        if row > 0:
            # Swap priorities
            rules[row].priority, rules[row-1].priority = rules[row-1].priority, rules[row].priority
            self.rule_manager.rules.sort(key=lambda r: r.priority)
            self.rule_manager.save()
            self.refresh_table()
    
    def move_rule_down(self, row):
        """Move rule down in priority"""
        rules = self.rule_manager.list_rules()
        if row < len(rules) - 1:
            # Swap priorities
            rules[row].priority, rules[row+1].priority = rules[row+1].priority, rules[row].priority
            self.rule_manager.rules.sort(key=lambda r: r.priority)
            self.rule_manager.save()
            self.refresh_table()
    
    def test_rule(self):
        """Open test rule dialog"""
        dialog = TestRuleDialog(self, self.rule_manager)
        dialog.exec()
    
    def apply_to_all(self):
        """Apply rules to all existing transactions"""
        # Get parent FinancialTracker to access bank
        parent = self.parent()
        if not parent or not hasattr(parent, 'bank'):
            QMessageBox.warning(self, 'Error', 'Cannot access transactions')
            return
        
        reply = QMessageBox.question(
            self,
            'Apply Rules',
            'Apply rules to all transactions?\n\nThis will categorize uncategorized transactions based on your rules.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            transactions = parent.bank.list_transactions(user_id=parent.current_user_id)
            stats = self.rule_manager.apply_to_all(transactions, overwrite=False)
            
            # Save updated transactions
            parent.bank.save()
            parent.refresh_data()
            
            QMessageBox.information(
                self,
                'Rules Applied',
                f'Categorized {stats["categorized"]} transactions\n'
                f'Skipped {stats["skipped"]} (already categorized)\n'
                f'Total: {stats["total"]}'
            )
    
    def show_statistics(self):
        """Show rule usage statistics"""
        stats = self.rule_manager.get_statistics()
        
        text = f"Total Rules: {stats['total_rules']}\n"
        text += f"Enabled: {stats['enabled_rules']}\n"
        text += f"Disabled: {stats['disabled_rules']}\n"
        text += f"Total Matches: {stats['total_matches']}\n\n"
        text += "Most Used Rules:\n"
        
        for i, rule in enumerate(stats['most_used'], 1):
            text += f"{i}. {rule.pattern} → {rule.category} ({rule.match_count} matches)\n"
        
        QMessageBox.information(self, 'Rule Statistics', text)


class AddRuleDialog(QDialog):
    """Dialog for adding or editing a transaction rule"""
    
    def __init__(self, parent=None, rule_manager=None, rule=None):
        super().__init__(parent)
        self.rule_manager = rule_manager
        self.rule = rule
        
        self.setWindowTitle('Edit Rule' if rule else 'Add Rule')
        self.setMinimumWidth(500)
        
        layout = QFormLayout()
        
        # Pattern
        self.pattern_edit = QLineEdit()
        if rule:
            self.pattern_edit.setText(rule.pattern)
        self.pattern_edit.setPlaceholderText('e.g., amazon, walmart, starbucks')
        layout.addRow('Pattern:', self.pattern_edit)
        
        # Match Type
        self.match_type_combo = QComboBox()
        self.match_type_combo.addItems(['Contains', 'Regex', 'Exact'])
        if rule:
            index = {'contains': 0, 'regex': 1, 'exact': 2}.get(rule.match_type, 0)
            self.match_type_combo.setCurrentIndex(index)
        layout.addRow('Match Type:', self.match_type_combo)
        
        # Category
        self.category_edit = QLineEdit()
        if rule:
            self.category_edit.setText(rule.category)
        self.category_edit.setPlaceholderText('e.g., Shopping, Groceries, Gas')
        layout.addRow('Category:', self.category_edit)
        
        # Type Filter
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Any', 'Income (in)', 'Expense (out)'])
        if rule:
            if rule.type == 'in':
                self.type_combo.setCurrentIndex(1)
            elif rule.type == 'out':
                self.type_combo.setCurrentIndex(2)
        layout.addRow('Transaction Type:', self.type_combo)
        
        # Enabled
        self.enabled_check = QCheckBox('Rule is enabled')
        self.enabled_check.setChecked(rule.enabled if rule else True)
        layout.addRow('', self.enabled_check)
        
        # Notes
        self.notes_edit = QLineEdit()
        if rule:
            self.notes_edit.setText(rule.notes)
        self.notes_edit.setPlaceholderText('Optional notes about this rule')
        layout.addRow('Notes:', self.notes_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def accept(self):
        """Validate and save rule"""
        pattern = self.pattern_edit.text().strip()
        category = self.category_edit.text().strip()
        
        if not pattern:
            QMessageBox.warning(self, 'Invalid Input', 'Pattern cannot be empty')
            return
        
        if not category:
            QMessageBox.warning(self, 'Invalid Input', 'Category cannot be empty')
            return
        
        # Get match type
        match_type_map = {0: 'contains', 1: 'regex', 2: 'exact'}
        match_type = match_type_map[self.match_type_combo.currentIndex()]
        
        # Get type filter
        type_map = {0: None, 1: 'in', 2: 'out'}
        type_filter = type_map[self.type_combo.currentIndex()]
        
        enabled = self.enabled_check.isChecked()
        notes = self.notes_edit.text().strip()
        
        if self.rule:
            # Update existing rule
            self.rule_manager.update_rule(
                self.rule.identifier,
                pattern=pattern,
                category=category,
                match_type=match_type,
                type=type_filter,
                enabled=enabled,
                notes=notes
            )
        else:
            # Add new rule
            self.rule_manager.add_rule(
                pattern=pattern,
                category=category,
                match_type=match_type,
                type_=type_filter,
                enabled=enabled,
                notes=notes
            )
        
        super().accept()


class TestRuleDialog(QDialog):
    """Dialog for testing transaction rules"""
    
    def __init__(self, parent=None, rule_manager=None):
        super().__init__(parent)
        self.rule_manager = rule_manager
        
        self.setWindowTitle('Test Transaction Rule')
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Info
        info_label = QLabel('Test how rules match against transaction descriptions:')
        layout.addWidget(info_label)
        
        # Test input
        form_layout = QFormLayout()
        
        self.test_input = QLineEdit()
        self.test_input.setPlaceholderText('Enter a transaction description to test')
        self.test_input.textChanged.connect(self.run_test)
        form_layout.addRow('Transaction Description:', self.test_input)
        
        layout.addLayout(form_layout)
        
        # Results
        results_label = QLabel('Matching Rules:')
        layout.addWidget(results_label)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(300)
        layout.addWidget(self.results_text)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def run_test(self):
        """Run test on input"""
        test_string = self.test_input.text()
        
        if not test_string:
            self.results_text.setPlainText('Enter a transaction description to test')
            return
        
        matches = self.rule_manager.get_suggestions(test_string)
        
        if not matches:
            self.results_text.setPlainText('No rules match this description')
            return
        
        result_text = f"Found {len(matches)} matching rule(s):\n\n"
        
        for i, rule in enumerate(matches, 1):
            result_text += f"{i}. Pattern: \"{rule.pattern}\" ({rule.match_type})\n"
            result_text += f"   Category: {rule.category}\n"
            result_text += f"   Type Filter: {rule.type if rule.type else 'Any'}\n"
            result_text += f"   Priority: {rule.priority + 1}\n"
            result_text += f"   Enabled: {'Yes' if rule.enabled else 'No'}\n"
            if rule.notes:
                result_text += f"   Notes: {rule.notes}\n"
            result_text += "\n"
        
        result_text += f"\n✓ First enabled rule will be applied: \"{matches[0].category}\""
        
        self.results_text.setPlainText(result_text)


class AddBudgetDialog(QDialog):
    """Dialog for adding or editing a budget"""
    
    def __init__(self, parent=None, budget=None):
        super().__init__(parent)
        self.budget = budget
        self.setWindowTitle('Edit Budget' if budget else 'Add Budget')
        self.setup_ui()
        
        if budget:
            self.load_budget_data()
    
    def setup_ui(self):
        layout = QFormLayout()
        
        # Category
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText('e.g., Groceries, Entertainment, Transportation')
        layout.addRow('Category:', self.category_edit)
        
        # Monthly Limit
        self.limit_spin = QDoubleSpinBox()
        self.limit_spin.setRange(0, 1000000)
        self.limit_spin.setDecimals(2)
        self.limit_spin.setPrefix('$')
        self.limit_spin.setValue(500.00)
        layout.addRow('Monthly Limit:', self.limit_spin)
        
        # Warning Threshold
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.01, 1.0)
        self.threshold_spin.setDecimals(2)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setValue(0.80)
        self.threshold_spin.setSuffix(' (80% = warning)')
        layout.addRow('Warning Threshold:', self.threshold_spin)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText('Optional notes about this budget...')
        layout.addRow('Notes:', self.notes_edit)
        
        # Info label
        info_label = QLabel('Budget colors:\n• Green: Under budget\n• Orange: Approaching limit (based on threshold)\n• Red: Over budget')
        info_label.setStyleSheet('color: #666; font-size: 11px; padding: 10px;')
        layout.addRow(info_label)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        self.setLayout(layout)
    
    def load_budget_data(self):
        """Load existing budget data into form"""
        if self.budget:
            self.category_edit.setText(self.budget.category)
            self.limit_spin.setValue(self.budget.monthly_limit)
            self.threshold_spin.setValue(self.budget.warning_threshold)
            self.notes_edit.setPlainText(self.budget.notes)
    
    def get_data(self):
        """Get budget data from form"""
        return {
            'category': self.category_edit.text().strip(),
            'monthly_limit': self.limit_spin.value(),
            'warning_threshold': self.threshold_spin.value(),
            'notes': self.notes_edit.toPlainText().strip()
        }


class AddGoalDialog(QDialog):
    """Dialog for adding or editing a goal"""
    
    def __init__(self, parent=None, goal_manager=None, goal=None):
        super().__init__(parent)
        self.goal_manager = goal_manager
        self.goal = goal
        
        self.setWindowTitle('Edit Goal' if goal else 'Add New Goal')
        self.setMinimumWidth(500)
        
        layout = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('e.g., Emergency Fund, Vacation, New Car')
        layout.addRow('Goal Name:', self.name_edit)
        
        # Icon selector
        icon_layout = QHBoxLayout()
        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText('💰')
        self.icon_edit.setMaximumWidth(60)
        icon_layout.addWidget(self.icon_edit)
        
        # Common icons
        icons = ['💰', '🏠', '��', '✈️', '🎓', '💍', '🏖️', '💻', '📱', '🎯']
        for icon in icons:
            btn = QPushButton(icon)
            btn.setMaximumWidth(35)
            btn.clicked.connect(lambda checked, i=icon: self.icon_edit.setText(i))
            icon_layout.addWidget(btn)
        
        icon_layout.addStretch()
        layout.addRow('Icon:', icon_layout)
        
        # Target amount
        self.target_spin = QDoubleSpinBox()
        self.target_spin.setRange(0, 1000000)
        self.target_spin.setDecimals(2)
        self.target_spin.setPrefix('$ ')
        self.target_spin.setValue(1000.00)
        layout.addRow('Target Amount:', self.target_spin)
        
        # Current amount (only for editing)
        if goal:
            self.current_spin = QDoubleSpinBox()
            self.current_spin.setRange(0, 1000000)
            self.current_spin.setDecimals(2)
            self.current_spin.setPrefix('$ ')
            layout.addRow('Current Amount:', self.current_spin)
        
        # Target date
        self.target_date_edit = QDateEdit()
        self.target_date_edit.setDate(QDate.currentDate().addMonths(12))
        self.target_date_edit.setCalendarPopup(True)
        self.target_date_edit.setDisplayFormat('yyyy-MM-dd')
        
        date_layout = QHBoxLayout()
        date_layout.addWidget(self.target_date_edit)
        
        no_date_check = QCheckBox('No target date')
        no_date_check.stateChanged.connect(lambda state: self.target_date_edit.setEnabled(state == 0))
        date_layout.addWidget(no_date_check)
        
        layout.addRow('Target Date:', date_layout)
        
        # Monthly contribution
        self.monthly_spin = QDoubleSpinBox()
        self.monthly_spin.setRange(0, 100000)
        self.monthly_spin.setDecimals(2)
        self.monthly_spin.setPrefix('$ ')
        layout.addRow('Monthly Contribution:', self.monthly_spin)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['low', 'medium', 'high', 'critical'])
        self.priority_combo.setCurrentText('medium')
        layout.addRow('Priority:', self.priority_combo)
        
        # Linked account (optional)
        self.account_combo = QComboBox()
        self.account_combo.addItem('None', None)
        # Add accounts if available
        if parent and hasattr(parent, 'account_manager'):
            accounts = parent.account_manager.list_accounts()
            for account in accounts:
                if account.user_id == parent.current_user_id and account.active:
                    self.account_combo.addItem(account.name, account.account_id)
        layout.addRow('Linked Account:', self.account_combo)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText('Optional notes about this goal...')
        layout.addRow('Notes:', self.notes_edit)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        self.setLayout(layout)
        
        # Load existing goal data
        if goal:
            self.load_goal_data()
    
    def load_goal_data(self):
        """Load existing goal data into form"""
        self.name_edit.setText(self.goal.name)
        self.icon_edit.setText(self.goal.icon)
        self.target_spin.setValue(self.goal.target_amount)
        if hasattr(self, 'current_spin'):
            self.current_spin.setValue(self.goal.current_amount)
        
        if self.goal.target_date:
            try:
                target_date = datetime.strptime(self.goal.target_date, '%Y-%m-%d')
                self.target_date_edit.setDate(QDate(target_date.year, target_date.month, target_date.day))
            except:
                pass
        
        self.monthly_spin.setValue(self.goal.monthly_contribution)
        self.priority_combo.setCurrentText(self.goal.priority)
        
        if self.goal.linked_account_id:
            index = self.account_combo.findData(self.goal.linked_account_id)
            if index >= 0:
                self.account_combo.setCurrentIndex(index)
        
        self.notes_edit.setPlainText(self.goal.notes)
    
    def get_data(self):
        """Get goal data from form"""
        data = {
            'name': self.name_edit.text().strip(),
            'icon': self.icon_edit.text().strip() or '💰',
            'target_amount': self.target_spin.value(),
            'target_date': self.target_date_edit.date().toString('yyyy-MM-dd') if self.target_date_edit.isEnabled() else None,
            'monthly_contribution': self.monthly_spin.value(),
            'priority': self.priority_combo.currentText(),
            'linked_account_id': self.account_combo.currentData(),
            'notes': self.notes_edit.toPlainText().strip()
        }
        
        if hasattr(self, 'current_spin'):
            data['current_amount'] = self.current_spin.value()
        
        return data


class ContributeToGoalDialog(QDialog):
    """Dialog for contributing to a goal"""
    
    def __init__(self, parent=None, goal=None):
        super().__init__(parent)
        self.goal = goal
        
        self.setWindowTitle(f'Contribute to {goal.name}')
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Goal info
        info_label = QLabel(
            f'<b>{goal.icon} {goal.name}</b><br>'
            f'Current: ${goal.current_amount:,.2f} / ${goal.target_amount:,.2f}<br>'
            f'Remaining: ${goal.get_remaining_amount():,.2f}'
        )
        info_label.setStyleSheet('padding: 10px; background-color: #f5f5f5; border-radius: 5px;')
        layout.addWidget(info_label)
        
        # Amount input
        form_layout = QFormLayout()
        
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, goal.get_remaining_amount() * 2)  # Allow overfunding
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix('$ ')
        self.amount_spin.setValue(min(goal.monthly_contribution, goal.get_remaining_amount()) if goal.monthly_contribution > 0 else 100.00)
        form_layout.addRow('Contribution Amount:', self.amount_spin)
        
        layout.addLayout(form_layout)
        
        # Quick amount buttons
        quick_layout = QHBoxLayout()
        quick_label = QLabel('Quick amounts:')
        quick_layout.addWidget(quick_label)
        
        if goal.monthly_contribution > 0:
            monthly_btn = QPushButton(f'${goal.monthly_contribution:,.2f}')
            monthly_btn.clicked.connect(lambda: self.amount_spin.setValue(goal.monthly_contribution))
            quick_layout.addWidget(monthly_btn)
        
        remaining = goal.get_remaining_amount()
        if remaining > 0:
            remaining_btn = QPushButton(f'${remaining:,.2f} (Complete)')
            remaining_btn.clicked.connect(lambda: self.amount_spin.setValue(remaining))
            quick_layout.addWidget(remaining_btn)
        
        quick_layout.addStretch()
        layout.addLayout(quick_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_amount(self):
        """Get contribution amount"""
        return self.amount_spin.value()


class GoalStatisticsDialog(QDialog):
    """Dialog showing goal statistics and analytics"""
    
    def __init__(self, parent=None, goal_manager=None, user_id=None):
        super().__init__(parent)
        self.goal_manager = goal_manager
        self.user_id = user_id
        
        self.setWindowTitle('Goal Statistics')
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # Overall statistics
        stats = self.goal_manager.get_statistics(user_id=user_id)
        
        stats_layout = QGridLayout()
        
        # Total goals
        total_label = QLabel(f'<h2>{stats["total_goals"]}</h2><p>Total Goals</p>')
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_label.setStyleSheet('background-color: #2196F3; color: white; padding: 15px; border-radius: 8px;')
        stats_layout.addWidget(total_label, 0, 0)
        
        # Active goals
        active_label = QLabel(f'<h2>{stats["active_goals"]}</h2><p>Active</p>')
        active_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        active_label.setStyleSheet('background-color: #ff9800; color: white; padding: 15px; border-radius: 8px;')
        stats_layout.addWidget(active_label, 0, 1)
        
        # Completed goals
        completed_label = QLabel(f'<h2>{stats["completed_goals"]}</h2><p>Completed</p>')
        completed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        completed_label.setStyleSheet('background-color: #4CAF50; color: white; padding: 15px; border-radius: 8px;')
        stats_layout.addWidget(completed_label, 0, 2)
        
        layout.addLayout(stats_layout)
        
        # Financial stats
        financial_group = QGroupBox('Financial Overview')
        financial_layout = QFormLayout()
        
        financial_layout.addRow('Total Target:', QLabel(f'${stats["total_target_amount"]:,.2f}'))
        financial_layout.addRow('Total Saved:', QLabel(f'${stats["total_saved_amount"]:,.2f}'))
        financial_layout.addRow('Total Remaining:', QLabel(f'${stats["total_remaining_amount"]:,.2f}'))
        financial_layout.addRow('Overall Progress:', QLabel(f'{stats["overall_progress_percentage"]:.1f}%'))
        financial_layout.addRow('Total Contributions:', QLabel(str(stats["total_contributions"])))
        
        financial_group.setLayout(financial_layout)
        layout.addWidget(financial_group)
        
        # Progress tracking
        progress_group = QGroupBox('Progress Tracking')
        progress_layout = QFormLayout()
        
        progress_layout.addRow('Goals On Track:', QLabel(f'{stats["goals_on_track"]} ✅'))
        progress_layout.addRow('Goals Behind:', QLabel(f'{stats["goals_behind"]} ⚠️'))
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Individual goal details
        goals_group = QGroupBox('Goal Details')
        goals_layout = QVBoxLayout()
        
        goals = self.goal_manager.list_goals(user_id=user_id, completed=False)
        for goal in goals:
            goal_info = QLabel(
                f'<b>{goal.icon} {goal.name}</b><br>'
                f'Progress: ${goal.current_amount:,.2f} / ${goal.target_amount:,.2f} ({goal.get_progress_percentage():.1f}%)<br>'
                f'Contributions: {goal.get_contribution_count()}'
            )
            goal_info.setStyleSheet('padding: 8px; background-color: #f5f5f5; border-radius: 4px; margin: 2px;')
            goals_layout.addWidget(goal_info)
        
        goals_group.setLayout(goals_layout)
        
        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidget(goals_group)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class NetWorthHistoryDialog(QDialog):
    """Dialog showing net worth history with ability to delete snapshots"""
    
    def __init__(self, tracker, user_id, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.user_id = user_id
        
        self.setWindowTitle('Net Worth History')
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Net Worth History')
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Date', 'Assets', 'Liabilities', 'Net Worth', 'Actions'])
        self.table.horizontalHeader().setStretchLastSection(False)
        
        self.populate_table()
        
        layout.addWidget(self.table)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def populate_table(self):
        """Populate table with snapshots"""
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
        
        self.table.setRowCount(0)
        
        snapshots = self.tracker.get_snapshots_for_user(self.user_id)
        snapshots.reverse()  # Show newest first
        
        for snapshot in snapshots:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Date
            date_item = QTableWidgetItem(snapshot.date)
            self.table.setItem(row, 0, date_item)
            
            # Assets
            assets_item = QTableWidgetItem(f'${snapshot.assets:,.2f}')
            assets_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            assets_item.setForeground(QBrush(QColor('#2e7d32')))
            self.table.setItem(row, 1, assets_item)
            
            # Liabilities
            liab_item = QTableWidgetItem(f'${snapshot.liabilities:,.2f}')
            liab_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            liab_item.setForeground(QBrush(QColor('#c62828')))
            self.table.setItem(row, 2, liab_item)
            
            # Net Worth
            nw_item = QTableWidgetItem(f'${snapshot.net_worth:,.2f}')
            nw_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            nw_item.setFont(QFont('Arial', 10, QFont.Weight.Bold))
            
            if snapshot.net_worth >= 0:
                nw_item.setForeground(QBrush(QColor('#2e7d32')))
            else:
                nw_item.setForeground(QBrush(QColor('#c62828')))
            
            self.table.setItem(row, 3, nw_item)
            
            # Delete button
            delete_btn = QPushButton('��️')
            delete_btn.clicked.connect(lambda checked, d=snapshot.date: self.delete_snapshot(d))
            self.table.setCellWidget(row, 4, delete_btn)
        
        self.table.resizeColumnsToContents()
    
    def delete_snapshot(self, snapshot_date):
        """Delete a snapshot"""
        reply = QMessageBox.question(
            self,
            'Confirm Delete',
            f'Are you sure you want to delete the snapshot from {snapshot_date}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.tracker.delete_snapshot(snapshot_date, self.user_id)
            self.populate_table()
            QMessageBox.information(self, 'Deleted', 'Snapshot deleted successfully.')


class TagManagerDialog(QDialog):
    """Dialog for managing tags"""
    
    def __init__(self, parent, tag_manager, transactions):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.transactions = transactions
        
        self.setWindowTitle('Tag Manager')
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Tag Management')
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Tags tab
        tags_tab = self.create_tags_tab()
        tabs.addTab(tags_tab, 'Tags')
        
        # Statistics tab
        stats_tab = self.create_statistics_tab()
        tabs.addTab(stats_tab, 'Statistics')
        
        layout.addWidget(tabs)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def create_tags_tab(self):
        """Create tags management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        add_btn = QPushButton('➕ Add Tag')
        add_btn.clicked.connect(self.add_tag)
        header_layout.addWidget(add_btn)
        
        import_btn = QPushButton('📥 Import')
        import_btn.clicked.connect(self.import_tags)
        header_layout.addWidget(import_btn)
        
        export_btn = QPushButton('📤 Export')
        export_btn.clicked.connect(self.export_tags)
        header_layout.addWidget(export_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Tags table
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
        self.tags_table = QTableWidget()
        self.tags_table.setColumnCount(5)
        self.tags_table.setHorizontalHeaderLabels(['Tag Name', 'Color', 'Description', 'Usage', 'Actions'])
        self.tags_table.horizontalHeader().setStretchLastSection(False)
        self.tags_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        self.populate_tags_table()
        
        layout.addWidget(self.tags_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_statistics_tab(self):
        """Create tag statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Get statistics
        stats = self.tag_manager.get_tag_statistics(self.transactions)
        
        # Summary stats
        summary_group = QGroupBox('Summary')
        summary_layout = QGridLayout()
        
        summary_layout.addWidget(QLabel('Total Tags:'), 0, 0)
        summary_layout.addWidget(QLabel(str(stats['total_tags'])), 0, 1)
        
        summary_layout.addWidget(QLabel('Used Tags:'), 0, 2)
        summary_layout.addWidget(QLabel(str(stats['used_tags'])), 0, 3)
        
        summary_layout.addWidget(QLabel('Unused Tags:'), 1, 0)
        summary_layout.addWidget(QLabel(str(stats['unused_tags'])), 1, 1)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Most used tags
        most_used_group = QGroupBox('Most Used Tags')
        most_used_layout = QVBoxLayout()
        
        for item in stats['most_used'][:5]:
            label = QLabel(f"{item['name']}: {item['count']} transactions")
            most_used_layout.addWidget(label)
        
        most_used_group.setLayout(most_used_layout)
        layout.addWidget(most_used_group)
        
        # Highest spending tags
        highest_spending_group = QGroupBox('Highest Spending by Tag')
        spending_layout = QVBoxLayout()
        
        for item in stats['highest_spending'][:5]:
            label = QLabel(f"{item['name']}: ${item['amount']:,.2f}")
            spending_layout.addWidget(label)
        
        highest_spending_group.setLayout(spending_layout)
        layout.addWidget(highest_spending_group)
        
        # Detailed table
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
        details_table = QTableWidget()
        details_table.setColumnCount(5)
        details_table.setHorizontalHeaderLabels(['Tag', 'Usage', 'Spending', 'Income', 'Net'])
        
        for detail in stats['tag_details']:
            if detail['usage_count'] == 0:
                continue  # Skip unused tags
            
            row = details_table.rowCount()
            details_table.insertRow(row)
            
            details_table.setItem(row, 0, QTableWidgetItem(detail['tag'].name))
            details_table.setItem(row, 1, QTableWidgetItem(str(detail['usage_count'])))
            details_table.setItem(row, 2, QTableWidgetItem(f"${detail['spending']:,.2f}"))
            details_table.setItem(row, 3, QTableWidgetItem(f"${detail['income']:,.2f}"))
            
            net_item = QTableWidgetItem(f"${detail['net']:,.2f}")
            if detail['net'] >= 0:
                net_item.setForeground(QBrush(QColor('#2e7d32')))
            else:
                net_item.setForeground(QBrush(QColor('#c62828')))
            details_table.setItem(row, 4, net_item)
        
        details_table.resizeColumnsToContents()
        layout.addWidget(details_table)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def populate_tags_table(self):
        """Populate tags table"""
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
        
        self.tags_table.setRowCount(0)
        
        # Update usage counts
        self.tag_manager.update_usage_counts(self.transactions)
        
        for tag in self.tag_manager.list_tags(sort_by='name'):
            row = self.tags_table.rowCount()
            self.tags_table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(tag.name)
            self.tags_table.setItem(row, 0, name_item)
            
            # Color preview
            color_widget = QWidget()
            color_layout = QHBoxLayout()
            color_layout.setContentsMargins(5, 2, 5, 2)
            
            color_preview = QLabel('     ')
            color_preview.setStyleSheet(f'background-color: {tag.color}; border: 1px solid #ccc; border-radius: 3px;')
            color_layout.addWidget(color_preview)
            
            color_label = QLabel(tag.color)
            color_layout.addWidget(color_label)
            color_layout.addStretch()
            
            color_widget.setLayout(color_layout)
            self.tags_table.setCellWidget(row, 1, color_widget)
            
            # Description
            desc_item = QTableWidgetItem(tag.description)
            self.tags_table.setItem(row, 2, desc_item)
            
            # Usage count
            usage_item = QTableWidgetItem(str(tag.usage_count))
            usage_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tags_table.setItem(row, 3, usage_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton('✏️')
            edit_btn.setMaximumWidth(40)
            edit_btn.clicked.connect(lambda checked, t=tag: self.edit_tag(t))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton('🗑️')
            delete_btn.setMaximumWidth(40)
            delete_btn.clicked.connect(lambda checked, t=tag: self.delete_tag(t))
            actions_layout.addWidget(delete_btn)
            
            actions_widget.setLayout(actions_layout)
            self.tags_table.setCellWidget(row, 4, actions_widget)
        
        self.tags_table.resizeColumnsToContents()
    
    def add_tag(self):
        """Add a new tag"""
        dialog = AddEditTagDialog(self, self.tag_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            tag = self.tag_manager.add_tag(data['name'], data['color'], data['description'])
            
            if tag:
                QMessageBox.information(self, 'Success', f'Tag "{tag.name}" created successfully!')
                self.populate_tags_table()
            else:
                QMessageBox.warning(self, 'Error', f'Tag "{data["name"]}" already exists.')
    
    def edit_tag(self, tag):
        """Edit an existing tag"""
        dialog = AddEditTagDialog(self, self.tag_manager, tag)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            success = self.tag_manager.update_tag(
                tag.tag_id,
                name=data['name'],
                color=data['color'],
                description=data['description']
            )
            
            if success:
                QMessageBox.information(self, 'Success', 'Tag updated successfully!')
                self.populate_tags_table()
            else:
                QMessageBox.warning(self, 'Error', 'Tag name already exists.')
    
    def delete_tag(self, tag):
        """Delete a tag"""
        # Count usage
        usage_count = sum(1 for tx in self.transactions if tag.name in tx.get('tags', []))
        
        message = f'Are you sure you want to delete the tag "{tag.name}"?'
        if usage_count > 0:
            message += f'\n\nThis tag is used in {usage_count} transaction(s).\nThe tag will be removed from all transactions.'
        
        reply = QMessageBox.question(
            self,
            'Confirm Delete',
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove tag from all transactions
            if usage_count > 0:
                for tx in self.transactions:
                    if 'tags' in tx and tag.name in tx['tags']:
                        tx['tags'].remove(tag.name)
                # Save updated transactions
                self.parent().bank.save()
            
            # Delete tag
            self.tag_manager.delete_tag(tag.tag_id)
            QMessageBox.information(self, 'Deleted', f'Tag "{tag.name}" deleted successfully.')
            self.populate_tags_table()
    
    def import_tags(self):
        """Import tags from CSV"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Import Tags',
            '',
            'CSV Files (*.csv)'
        )
        
        if file_path:
            count = self.tag_manager.import_tags(file_path)
            QMessageBox.information(self, 'Import Complete', f'Imported {count} new tag(s).')
            self.populate_tags_table()
    
    def export_tags(self):
        """Export tags to CSV"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Export Tags',
            'tags.csv',
            'CSV Files (*.csv)'
        )
        
        if file_path:
            success = self.tag_manager.export_tags(file_path)
            if success:
                QMessageBox.information(self, 'Export Successful', f'Tags exported to:\n{file_path}')
            else:
                QMessageBox.critical(self, 'Export Failed', 'Failed to export tags.')


class AddEditTagDialog(QDialog):
    """Dialog for adding/editing a tag"""
    
    def __init__(self, parent, tag_manager, tag=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.tag = tag
        
        self.setWindowTitle('Edit Tag' if tag else 'Add Tag')
        self.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('e.g., tax-deductible')
        if tag:
            self.name_edit.setText(tag.name)
        layout.addRow('Tag Name:', self.name_edit)
        
        # Color picker
        color_layout = QHBoxLayout()
        
        self.color_edit = QLineEdit()
        self.color_edit.setText(tag.color if tag else '#808080')
        self.color_edit.setMaximumWidth(100)
        color_layout.addWidget(self.color_edit)
        
        from PyQt6.QtWidgets import QColorDialog
        pick_color_btn = QPushButton('Pick Color')
        pick_color_btn.clicked.connect(self.pick_color)
        color_layout.addWidget(pick_color_btn)
        
        # Color preview
        self.color_preview = QLabel('     ')
        self.update_color_preview()
        color_layout.addWidget(self.color_preview)
        
        color_layout.addStretch()
        layout.addRow('Color:', color_layout)
        
        # Preset colors
        presets_layout = QHBoxLayout()
        preset_colors = ['#F44336', '#E91E63', '#9C27B0', '#673AB7', '#3F51B5', '#2196F3',
                        '#03A9F4', '#00BCD4', '#009688', '#4CAF50', '#8BC34A', '#CDDC39',
                        '#FFEB3B', '#FFC107', '#FF9800', '#FF5722', '#795548', '#9E9E9E']
        
        for color in preset_colors:
            btn = QPushButton()
            btn.setMaximumSize(25, 25)
            btn.setStyleSheet(f'background-color: {color}; border: 1px solid #ccc;')
            btn.clicked.connect(lambda checked, c=color: self.set_color(c))
            presets_layout.addWidget(btn)
        
        presets_layout.addStretch()
        layout.addRow('Presets:', presets_layout)
        
        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText('Optional description...')
        if tag:
            self.desc_edit.setPlainText(tag.description)
        layout.addRow('Description:', self.desc_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def pick_color(self):
        """Open color picker dialog"""
        from PyQt6.QtWidgets import QColorDialog
        
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_color(color.name())
    
    def set_color(self, color):
        """Set the color"""
        self.color_edit.setText(color)
        self.update_color_preview()
    
    def update_color_preview(self):
        """Update color preview"""
        color = self.color_edit.text()
        self.color_preview.setStyleSheet(f'background-color: {color}; border: 1px solid #ccc; border-radius: 3px;')
    
    def get_data(self):
        """Get form data"""
        return {
            'name': self.name_edit.text().strip(),
            'color': self.color_edit.text(),
            'description': self.desc_edit.toPlainText().strip()
        }


class LoanDetailsDialog(QDialog):
    """Dialog showing full amortization schedule for a loan"""
    
    def __init__(self, loan, parent=None):
        super().__init__(parent)
        self.loan = loan
        self.setWindowTitle(f"Loan Details: {loan.desc}")
        self.resize(1000, 700)
        
        layout = QVBoxLayout()
        
        # Loan summary
        summary_group = QGroupBox("Loan Summary")
        summary_layout = QGridLayout()
        
        stats = loan.get_summary_stats()
        
        summary_layout.addWidget(QLabel('<b>Principal:</b>'), 0, 0)
        summary_layout.addWidget(QLabel(f"${loan.principal:,.2f}"), 0, 1)
        
        summary_layout.addWidget(QLabel('<b>Interest Rate:</b>'), 0, 2)
        summary_layout.addWidget(QLabel(f"{loan.annual_rate * 100:.2f}%"), 0, 3)
        
        summary_layout.addWidget(QLabel('<b>Monthly Payment:</b>'), 1, 0)
        summary_layout.addWidget(QLabel(f"${loan.minimum_payment:,.2f}"), 1, 1)
        
        summary_layout.addWidget(QLabel('<b>Remaining Balance:</b>'), 1, 2)
        summary_layout.addWidget(QLabel(f"${loan.remaining_principal:,.2f}"), 1, 3)
        
        summary_layout.addWidget(QLabel('<b>Total Interest:</b>'), 2, 0)
        summary_layout.addWidget(QLabel(f"${stats['total_interest']:,.2f}"), 2, 1)
        
        summary_layout.addWidget(QLabel('<b>Payoff Date:</b>'), 2, 2)
        payoff_date = datetime.strptime(stats['payoff_date'], '%Y-%m-%d').strftime('%B %d, %Y')
        summary_layout.addWidget(QLabel(payoff_date), 2, 3)
        
        summary_layout.addWidget(QLabel('<b>Months to Payoff:</b>'), 3, 0)
        summary_layout.addWidget(QLabel(f"{stats['months_to_payoff']} months ({stats['months_to_payoff'] / 12:.1f} years)"), 3, 1, 1, 3)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Tabs for different views
        tabs = QTabWidget()
        
        # Amortization schedule tab
        schedule_widget = QWidget()
        schedule_layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        
        export_btn = QPushButton('Export to CSV')
        export_btn.clicked.connect(self.export_schedule)
        controls.addWidget(export_btn)
        
        what_if_btn = QPushButton('What-If Calculator')
        what_if_btn.clicked.connect(self.open_what_if)
        controls.addWidget(what_if_btn)
        
        controls.addStretch()
        schedule_layout.addLayout(controls)
        
        # Schedule table
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(7)
        self.schedule_table.setHorizontalHeaderLabels([
            'Payment #', 'Date', 'Payment', 'Principal', 'Interest', 'Extra', 'Balance'
        ])
        
        # Populate schedule
        schedule = loan.get_amortization_schedule()
        self.schedule_table.setRowCount(len(schedule))
        
        for row, payment in enumerate(schedule):
            self.schedule_table.setItem(row, 0, QTableWidgetItem(str(payment['payment_number'])))
            
            payment_date = datetime.strptime(payment['date'], '%Y-%m-%d').strftime('%m/%d/%Y')
            self.schedule_table.setItem(row, 1, QTableWidgetItem(payment_date))
            
            self.schedule_table.setItem(row, 2, QTableWidgetItem(f"${payment['payment']:,.2f}"))
            self.schedule_table.setItem(row, 3, QTableWidgetItem(f"${payment['principal']:,.2f}"))
            self.schedule_table.setItem(row, 4, QTableWidgetItem(f"${payment['interest']:,.2f}"))
            self.schedule_table.setItem(row, 5, QTableWidgetItem(f"${payment['extra_principal']:,.2f}"))
            self.schedule_table.setItem(row, 6, QTableWidgetItem(f"${payment['balance']:,.2f}"))
        
        header = self.schedule_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        schedule_layout.addWidget(self.schedule_table)
        schedule_widget.setLayout(schedule_layout)
        tabs.addTab(schedule_widget, 'Payment Schedule')
        
        # Chart tab
        chart_widget = QWidget()
        chart_layout = QVBoxLayout()
        
        # Create chart
        figure = Figure(figsize=(10, 6))
        canvas = FigureCanvas(figure)
        
        ax1 = figure.add_subplot(211)
        ax2 = figure.add_subplot(212)
        
        # Principal vs Interest chart
        payments = [p['payment_number'] for p in schedule]
        principal = [p['principal'] for p in schedule]
        interest = [p['interest'] for p in schedule]
        
        ax1.bar(payments, principal, label='Principal', color='#4CAF50')
        ax1.bar(payments, interest, bottom=principal, label='Interest', color='#F44336')
        ax1.set_xlabel('Payment Number')
        ax1.set_ylabel('Amount ($)')
        ax1.set_title('Principal vs Interest per Payment')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Balance over time
        balances = [p['balance'] for p in schedule]
        ax2.plot(payments, balances, color='#2196F3', linewidth=2)
        ax2.fill_between(payments, balances, alpha=0.3, color='#2196F3')
        ax2.set_xlabel('Payment Number')
        ax2.set_ylabel('Balance ($)')
        ax2.set_title('Remaining Balance Over Time')
        ax2.grid(True, alpha=0.3)
        
        figure.tight_layout()
        
        chart_layout.addWidget(canvas)
        chart_widget.setLayout(chart_layout)
        tabs.addTab(chart_widget, 'Charts')
        
        layout.addWidget(tabs)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def export_schedule(self):
        """Export schedule to CSV"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            'Export Amortization Schedule',
            f"{self.loan.desc}_schedule.csv",
            'CSV Files (*.csv)'
        )
        
        if filename:
            from src.loan_calculator import LoanCalculator
            
            calculator = LoanCalculator(
                principal=self.loan.remaining_principal,
                annual_rate=self.loan.annual_rate,
                monthly_payment=self.loan.minimum_payment,
                start_date=date.fromisoformat(self.loan.start_date)
            )
            
            schedule = calculator.calculate_standard_schedule()
            success = calculator.export_schedule_to_csv(schedule, filename)
            
            if success:
                QMessageBox.information(self, 'Success', f'Schedule exported to {filename}')
            else:
                QMessageBox.warning(self, 'Error', 'Failed to export schedule')
    
    def open_what_if(self):
        """Open what-if calculator"""
        dialog = WhatIfCalculatorDialog(self.loan, self)
        dialog.exec()


class WhatIfCalculatorDialog(QDialog):
    """What-if calculator for loan payoff scenarios"""
    
    def __init__(self, loan, parent=None):
        super().__init__(parent)
        self.loan = loan
        self.setWindowTitle(f"What-If Calculator: {loan.desc}")
        self.resize(900, 650)
        
        layout = QVBoxLayout()
        
        # Current loan info
        info_group = QGroupBox("Current Loan")
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel('<b>Remaining Balance:</b>'), 0, 0)
        info_layout.addWidget(QLabel(f"${loan.remaining_principal:,.2f}"), 0, 1)
        
        info_layout.addWidget(QLabel('<b>Interest Rate:</b>'), 0, 2)
        info_layout.addWidget(QLabel(f"{loan.annual_rate * 100:.2f}%"), 0, 3)
        
        info_layout.addWidget(QLabel('<b>Monthly Payment:</b>'), 1, 0)
        info_layout.addWidget(QLabel(f"${loan.minimum_payment:,.2f}"), 1, 1)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Scenario inputs
        scenario_group = QGroupBox("Payment Scenarios")
        scenario_layout = QFormLayout()
        
        self.extra_monthly = QDoubleSpinBox()
        self.extra_monthly.setRange(0, 100000)
        self.extra_monthly.setPrefix('$')
        self.extra_monthly.setValue(0)
        scenario_layout.addRow('Extra Monthly Payment:', self.extra_monthly)
        
        self.lump_sum = QDoubleSpinBox()
        self.lump_sum.setRange(0, 1000000)
        self.lump_sum.setPrefix('$')
        self.lump_sum.setValue(0)
        scenario_layout.addRow('One-Time Lump Sum:', self.lump_sum)
        
        self.lump_sum_month = QComboBox()
        self.lump_sum_month.addItem('No lump sum', 0)
        for i in range(1, 121):  # Up to 10 years
            self.lump_sum_month.addItem(f'Payment #{i}', i)
        scenario_layout.addRow('Apply Lump Sum At:', self.lump_sum_month)
        
        calculate_btn = QPushButton('Calculate Scenarios')
        calculate_btn.clicked.connect(self.calculate_scenarios)
        scenario_layout.addRow(calculate_btn)
        
        scenario_group.setLayout(scenario_layout)
        layout.addWidget(scenario_group)
        
        # Results display
        self.results_group = QGroupBox("Comparison Results")
        self.results_layout = QVBoxLayout()
        self.results_group.setLayout(self.results_layout)
        layout.addWidget(self.results_group)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # Calculate initial scenario
        self.calculate_scenarios()
    
    def calculate_scenarios(self):
        """Calculate and display payment scenarios"""
        # Clear previous results
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get scenario parameters
        extra_monthly = self.extra_monthly.value()
        lump_sum = self.lump_sum.value()
        lump_sum_month = self.lump_sum_month.currentData()
        
        # Calculate comparison
        comparison = self.loan.compare_payment_scenarios(extra_monthly, lump_sum, lump_sum_month)
        
        # Create comparison table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            'Scenario', 'Total Interest', 'Months to Payoff', 'Payoff Date', 'Total Paid'
        ])
        table.setRowCount(2)
        
        # Standard scenario
        std = comparison['standard']
        table.setItem(0, 0, QTableWidgetItem('Current Plan'))
        table.setItem(0, 1, QTableWidgetItem(f"${std['total_interest']:,.2f}"))
        table.setItem(0, 2, QTableWidgetItem(f"{std['months_to_payoff']} ({std['months_to_payoff'] / 12:.1f} years)"))
        payoff_date = datetime.strptime(std['payoff_date'], '%Y-%m-%d').strftime('%B %Y')
        table.setItem(0, 3, QTableWidgetItem(payoff_date))
        table.setItem(0, 4, QTableWidgetItem(f"${std['total_paid']:,.2f}"))
        
        # Accelerated scenario
        acc = comparison['accelerated']
        table.setItem(1, 0, QTableWidgetItem('Accelerated Plan'))
        table.setItem(1, 1, QTableWidgetItem(f"${acc['total_interest']:,.2f}"))
        table.setItem(1, 2, QTableWidgetItem(f"{acc['months_to_payoff']} ({acc['months_to_payoff'] / 12:.1f} years)"))
        payoff_date = datetime.strptime(acc['payoff_date'], '%Y-%m-%d').strftime('%B %Y')
        table.setItem(1, 3, QTableWidgetItem(payoff_date))
        table.setItem(1, 4, QTableWidgetItem(f"${acc['total_paid']:,.2f}"))
        
        header = table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        table.setMaximumHeight(120)
        self.results_layout.addWidget(table)
        
        # Savings summary
        savings_label = QLabel()
        savings_html = f'''
        <div style="padding: 15px; background-color: #E8F5E9; border-radius: 5px; margin-top: 10px;">
            <h3 style="color: #2E7D32; margin: 0 0 10px 0;">💰 Potential Savings</h3>
            <p style="margin: 5px 0;"><b>Interest Saved:</b> <span style="color: #2E7D32; font-size: 16px;">${comparison['interest_saved']:,.2f}</span></p>
            <p style="margin: 5px 0;"><b>Time Saved:</b> <span style="color: #2E7D32; font-size: 16px;">{comparison['months_saved']} months ({comparison['years_saved']:.1f} years)</span></p>
        </div>
        '''
        savings_label.setText(savings_html)
        self.results_layout.addWidget(savings_label)
        
        # Chart
        figure = Figure(figsize=(8, 4))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        
        scenarios = ['Current\nPlan', 'Accelerated\nPlan']
        interests = [std['total_interest'], acc['total_interest']]
        
        bars = ax.bar(scenarios, interests, color=['#F44336', '#4CAF50'])
        ax.set_ylabel('Total Interest Paid ($)')
        ax.set_title('Interest Comparison')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'${height:,.0f}',
                   ha='center', va='bottom')
        
        figure.tight_layout()
        self.results_layout.addWidget(canvas)


class RecurringHistoryDialog(QDialog):
    """Dialog showing history of instances created by a recurring transaction"""
    
    def __init__(self, recurring_tx, bank, parent=None):
        super().__init__(parent)
        self.recurring_tx = recurring_tx
        self.bank = bank
        self.setWindowTitle(f"History: {recurring_tx['desc']}")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Summary
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(QLabel(f"<b>Recurring Transaction:</b> {recurring_tx['desc']}"))
        summary_layout.addStretch()
        instances = recurring_tx.get('instances_created', [])
        summary_layout.addWidget(QLabel(f"<b>Total Instances:</b> {len(instances)}"))
        layout.addLayout(summary_layout)
        
        # History table
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['Date', 'Amount', 'Category', 'Account'])
        
        # Get instances
        table.setRowCount(len(instances))
        for row, instance_date in enumerate(sorted(instances, reverse=True)):
            table.setItem(row, 0, QTableWidgetItem(instance_date))
            
            # Show amount (handle variable amounts)
            amount_type = recurring_tx.get('amount_type', 'fixed')
            if amount_type == 'variable':
                amount_text = f"${recurring_tx.get('amount_min', 0):.2f} - ${recurring_tx.get('amount_max', 0):.2f}"
            else:
                amount_text = f"${recurring_tx.get('amount', 0):.2f}"
            table.setItem(row, 1, QTableWidgetItem(amount_text))
            
            table.setItem(row, 2, QTableWidgetItem(recurring_tx.get('category', 'N/A')))
            table.setItem(row, 3, QTableWidgetItem(recurring_tx.get('account', 'N/A')))
        
        header = table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(table)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class RecurringCalendarDialog(QDialog):
    """Calendar view showing upcoming recurring transactions for the next 30 days"""
    
    def __init__(self, bank, user_id, parent=None):
        super().__init__(parent)
        self.bank = bank
        self.user_id = user_id
        self.setWindowTitle("Recurring Transactions Calendar (Next 30 Days)")
        self.resize(1000, 700)
        
        layout = QVBoxLayout()
        
        # Date range display
        from datetime import date, timedelta
        today = date.today()
        end_date = today + timedelta(days=30)
        date_label = QLabel(f"<h3>📅 {today.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}</h3>")
        layout.addWidget(date_label)
        
        # Get all recurring transactions
        recurring_txs = bank.list_recurring_transactions(user_id)
        
        # Calendar table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['Date', 'Description', 'Amount', 'Category', 'Days Until'])
        
        # Collect all upcoming dates
        from src.bank import RecurringTransaction
        upcoming_items = []
        
        for rtx in recurring_txs:
            recurring_obj = RecurringTransaction.from_dict(rtx)
            
            # Skip paused or completed
            if rtx.get('status') in ['paused', 'completed']:
                continue
            
            # Get upcoming dates
            upcoming_dates = recurring_obj.get_upcoming_dates(days=30)
            
            for due_date in upcoming_dates:
                # Determine amount display
                amount_type = rtx.get('amount_type', 'fixed')
                if amount_type == 'variable' and rtx.get('amount_min') and rtx.get('amount_max'):
                    amount_text = f"${rtx['amount_min']:.2f} - ${rtx['amount_max']:.2f}"
                elif amount_type == 'prompt':
                    amount_text = 'Prompt'
                else:
                    amount_text = f"${rtx['amount']:.2f}"
                
                days_until = (due_date - today).days
                
                upcoming_items.append({
                    'date': due_date,
                    'desc': rtx['desc'],
                    'amount': amount_text,
                    'category': rtx.get('category', 'N/A'),
                    'days_until': days_until,
                    'type': rtx.get('type', 'out')
                })
        
        # Sort by date
        upcoming_items.sort(key=lambda x: x['date'])
        
        # Populate table
        table.setRowCount(len(upcoming_items))
        for row, item in enumerate(upcoming_items):
            # Date
            date_item = QTableWidgetItem(item['date'].strftime('%Y-%m-%d (%A)'))
            table.setItem(row, 0, date_item)
            
            # Description
            desc_item = QTableWidgetItem(item['desc'])
            # Color code by type
            if item['type'] == 'in':
                desc_item.setForeground(QBrush(QColor('#4CAF50')))  # Green for income
            else:
                desc_item.setForeground(QBrush(QColor('#F44336')))  # Red for expense
            table.setItem(row, 1, desc_item)
            
            # Amount
            table.setItem(row, 2, QTableWidgetItem(item['amount']))
            
            # Category
            table.setItem(row, 3, QTableWidgetItem(item['category']))
            
            # Days Until
            days_item = QTableWidgetItem(f"{item['days_until']} days")
            if item['days_until'] <= 1:
                days_item.setForeground(QBrush(QColor('#F44336')))  # Red for imminent
            elif item['days_until'] <= 7:
                days_item.setForeground(QBrush(QColor('#FFA500')))  # Orange for soon
            table.setItem(row, 4, days_item)
        
        header = table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(table)
        
        # Summary
        total_income = sum(
            float(item['amount'].replace('$', '').split(' - ')[0])
            for item in upcoming_items
            if item['type'] == 'in' and item['amount'] not in ['Prompt']
        )
        total_expense = sum(
            float(item['amount'].replace('$', '').split(' - ')[0])
            for item in upcoming_items
            if item['type'] != 'in' and item['amount'] not in ['Prompt']
        )
        
        summary_label = QLabel(
            f"<div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px;'>"
            f"<b>30-Day Summary:</b> {len(upcoming_items)} transactions | "
            f"<span style='color: #4CAF50;'>Income: ${total_income:,.2f}</span> | "
            f"<span style='color: #F44336;'>Expenses: ${total_expense:,.2f}</span> | "
            f"Net: ${(total_income - total_expense):,.2f}"
            f"</div>"
        )
        layout.addWidget(summary_label)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class UpcomingRecurringDialog(QDialog):
    """Dialog showing upcoming recurring transactions in the next 7 days"""
    
    def __init__(self, bank, user_id, parent=None):
        super().__init__(parent)
        self.bank = bank
        self.user_id = user_id
        self.setWindowTitle("🔔 Upcoming Recurring Transactions (Next 7 Days)")
        self.resize(700, 500)
        
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("<h3>Recurring transactions due in the next 7 days:</h3>")
        layout.addWidget(info_label)
        
        # Get all recurring transactions
        recurring_txs = bank.list_recurring_transactions(user_id)
        
        # List of upcoming
        from src.bank import RecurringTransaction
        from datetime import date, timedelta
        today = date.today()
        upcoming_items = []
        
        for rtx in recurring_txs:
            recurring_obj = RecurringTransaction.from_dict(rtx)
            
            # Skip paused or completed
            if rtx.get('status') in ['paused', 'completed']:
                continue
            
            # Skip if skip_next is set
            if rtx.get('skip_next'):
                continue
            
            # Get upcoming dates (7 days)
            upcoming_dates = recurring_obj.get_upcoming_dates(days=7)
            
            for due_date in upcoming_dates:
                # Determine amount display
                amount_type = rtx.get('amount_type', 'fixed')
                if amount_type == 'variable' and rtx.get('amount_min') and rtx.get('amount_max'):
                    amount_text = f"${rtx['amount_min']:.2f} - ${rtx['amount_max']:.2f}"
                elif amount_type == 'prompt':
                    amount_text = 'You will be prompted'
                else:
                    amount_text = f"${rtx['amount']:.2f}"
                
                days_until = (due_date - today).days
                
                upcoming_items.append({
                    'date': due_date,
                    'desc': rtx['desc'],
                    'amount': amount_text,
                    'days_until': days_until,
                    'type': rtx.get('type', 'out')
                })
        
        # Sort by date
        upcoming_items.sort(key=lambda x: x['date'])
        
        if not upcoming_items:
            layout.addWidget(QLabel("<p style='color: #4CAF50;'>✓ No recurring transactions due in the next 7 days</p>"))
        else:
            # Create notification cards
            for item in upcoming_items:
                card = QGroupBox()
                card_layout = QVBoxLayout()
                
                # Date and days until
                if item['days_until'] == 0:
                    date_text = f"<b style='color: #F44336;'>TODAY - {item['date'].strftime('%B %d, %Y')}</b>"
                elif item['days_until'] == 1:
                    date_text = f"<b style='color: #FFA500;'>TOMORROW - {item['date'].strftime('%B %d, %Y')}</b>"
                else:
                    date_text = f"<b>In {item['days_until']} days - {item['date'].strftime('%B %d, %Y')}</b>"
                
                card_layout.addWidget(QLabel(date_text))
                
                # Description
                desc_label = QLabel(f"<h4>{item['desc']}</h4>")
                card_layout.addWidget(desc_label)
                
                # Amount
                amount_label = QLabel(f"Amount: {item['amount']}")
                card_layout.addWidget(amount_label)
                
                # Type indicator
                type_text = '💰 Income' if item['type'] == 'in' else '💸 Expense'
                card_layout.addWidget(QLabel(type_text))
                
                card.setLayout(card_layout)
                
                # Color code by urgency
                if item['days_until'] <= 1:
                    card.setStyleSheet('QGroupBox { background-color: #FFEBEE; border: 2px solid #F44336; border-radius: 5px; padding: 10px; }')
                elif item['days_until'] <= 3:
                    card.setStyleSheet('QGroupBox { background-color: #FFF3E0; border: 2px solid #FFA500; border-radius: 5px; padding: 10px; }')
                else:
                    card.setStyleSheet('QGroupBox { background-color: #E8F5E9; border: 2px solid #4CAF50; border-radius: 5px; padding: 10px; }')
                
                layout.addWidget(card)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

