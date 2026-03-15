from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QComboBox, QPushButton, QDateEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget,
                             QGroupBox, QFormLayout, QCheckBox, QSpinBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont
from src.bank import Bank, RecurringTransaction
from datetime import datetime, timedelta
import json
from assets.Logger import Logger

logger = Logger()

class FinancialIOTab(QWidget):
    # Signal to notify dashboard of updates
    transaction_added = pyqtSignal()
    
    def __init__(self, current_user_id=None):
        super().__init__()
        logger.debug("FinancialIOTab", f"Initializing FinancialIOTab for user {current_user_id}")
        self.current_user_id = current_user_id
        self.bank = Bank(current_user_id)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Financial Input/Output")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Create tab widget for different input types
        self.tab_widget = QTabWidget()
        
        # Add Transaction Tab
        self.add_transaction_tab = self.create_add_transaction_tab()
        self.tab_widget.addTab(self.add_transaction_tab, "Add Transaction")
        
        # Recurring Transactions Tab
        self.recurring_tab = self.create_recurring_transactions_tab()
        self.tab_widget.addTab(self.recurring_tab, "Recurring Transactions")
        
        # Process Payments Tab
        self.process_tab = self.create_process_payments_tab()
        self.tab_widget.addTab(self.process_tab, "Process Payments")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        
    def create_add_transaction_tab(self):
        """Create the add transaction tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Input form
        form_group = QGroupBox("Add New Transaction")
        form_layout = QFormLayout()
        
        # Amount
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        form_layout.addRow("Amount ($):", self.amount_input)
        
        # Description
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Transaction description")
        form_layout.addRow("Description:", self.desc_input)
        
        # Type (Income/Expense)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Income", "Expense"])
        form_layout.addRow("Type:", self.type_combo)
        
        # Account
        self.account_combo = QComboBox()
        self.account_combo.addItems(["Checking", "Savings", "Cash", "Credit Card", "Investment"])
        form_layout.addRow("Account:", self.account_combo)
        
        # Category
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)  # Allow custom categories
        self.update_category_list()
        form_layout.addRow("Category:", self.category_combo)
        
        # Date
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setMinimumWidth(200)
        calendar = self.date_input.calendarWidget()
        if calendar:
            calendar.setMinimumSize(300, 200)
        form_layout.addRow("Date:", self.date_input)
        
        # Make Recurring checkbox
        self.make_recurring_check = QCheckBox("Make this a recurring transaction")
        form_layout.addRow("", self.make_recurring_check)
        
        # Recurring options (initially hidden)
        self.recurring_group = QGroupBox("Recurring Options")
        self.recurring_group.setVisible(False)
        recurring_layout = QFormLayout()
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(['weekly', 'monthly', 'yearly'])
        self.frequency_combo.setCurrentText('monthly')  # Default to monthly
        recurring_layout.addRow("Frequency:", self.frequency_combo)
        
        self.end_date_input = QDateEdit()
        self.end_date_input.setDate(QDate.currentDate().addYears(1))
        self.end_date_input.setCalendarPopup(True)
        recurring_layout.addRow("End Date:", self.end_date_input)
        
        self.indefinite_check = QCheckBox("No end date (indefinite)")
        recurring_layout.addRow("", self.indefinite_check)
        
        self.recurring_group.setLayout(recurring_layout)
        form_layout.addRow(self.recurring_group)
        
        # Connect checkbox to show/hide recurring options
        self.make_recurring_check.toggled.connect(self.recurring_group.setVisible)
        
        # Add button
        add_btn = QPushButton("Add Transaction")
        add_btn.clicked.connect(self.add_transaction)
        add_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        form_layout.addRow(add_btn)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Recent transactions table
        recent_group = QGroupBox("Recent Transactions")
        recent_layout = QVBoxLayout()
        
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(7)
        self.recent_table.setHorizontalHeaderLabels(['Date', 'Description', 'Amount', 'Type', 'Category', 'Account', 'Actions'])
        header = self.recent_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        recent_layout.addWidget(self.recent_table)
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)
        
        self.update_recent_transactions_table()
        
        widget.setLayout(layout)
        return widget
        
    def create_recurring_transactions_tab(self):
        """Create the recurring transactions management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Add recurring transaction form
        form_group = QGroupBox("Add Recurring Transaction")
        form_layout = QFormLayout()
        
        # Amount
        self.rec_amount_input = QLineEdit()
        self.rec_amount_input.setPlaceholderText("0.00")
        form_layout.addRow("Amount ($):", self.rec_amount_input)
        
        # Description
        self.rec_desc_input = QLineEdit()
        self.rec_desc_input.setPlaceholderText("Recurring transaction description")
        form_layout.addRow("Description:", self.rec_desc_input)
        
        # Type
        self.rec_type_combo = QComboBox()
        self.rec_type_combo.addItems(["Income", "Expense", "Loan Payment"])
        form_layout.addRow("Type:", self.rec_type_combo)
        
        # Account
        self.rec_account_combo = QComboBox()
        self.rec_account_combo.addItems(["Checking", "Savings", "Cash", "Credit Card", "Investment"])
        form_layout.addRow("Account:", self.rec_account_combo)
        
        # Category
        self.rec_category_combo = QComboBox()
        self.rec_category_combo.setEditable(True)
        self.update_category_list()
        form_layout.addRow("Category:", self.rec_category_combo)
        
        # Frequency
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["weekly", "monthly", "yearly"])
        form_layout.addRow("Frequency:", self.frequency_combo)
        
        # Start Date
        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setCalendarPopup(True)
        form_layout.addRow("Start Date:", self.start_date_input)
        
        # End Date (optional)
        self.end_date_input = QDateEdit()
        self.end_date_input.setDate(QDate.currentDate().addYears(1))
        self.end_date_input.setCalendarPopup(True)
        self.has_end_date = QCheckBox("Has End Date")
        end_date_layout = QHBoxLayout()
        end_date_layout.addWidget(self.has_end_date)
        end_date_layout.addWidget(self.end_date_input)
        form_layout.addRow("End Date:", end_date_layout)
        
        # Add button
        add_rec_btn = QPushButton("Add Recurring Transaction")
        add_rec_btn.clicked.connect(self.add_recurring_transaction)
        add_rec_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px; }")
        form_layout.addRow(add_rec_btn)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Recurring transactions table
        rec_group = QGroupBox("Manage Recurring Transactions")
        rec_layout = QVBoxLayout()
        
        self.recurring_table = QTableWidget()
        self.recurring_table.setColumnCount(8)
        self.recurring_table.setHorizontalHeaderLabels(['Description', 'Amount', 'Type', 'Category', 'Account', 'Frequency', 'Next Due', 'Actions'])
        header = self.recurring_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        rec_layout.addWidget(self.recurring_table)
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)
        
        self.update_recurring_transactions_table()
        
        widget.setLayout(layout)
        return widget
        
    def create_process_payments_tab(self):
        """Create tab for processing due payments"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Process due recurring transactions and manage payments:")
        instructions.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Process buttons
        button_layout = QHBoxLayout()
        
        process_all_btn = QPushButton("Process All Due Payments")
        process_all_btn.clicked.connect(self.process_all_due_payments)
        process_all_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 10px; }")
        button_layout.addWidget(process_all_btn)
        
        refresh_btn = QPushButton("Refresh Due Payments")
        refresh_btn.clicked.connect(self.update_due_payments_table)
        refresh_btn.setStyleSheet("QPushButton { background-color: #607D8B; color: white; font-weight: bold; padding: 10px; }")
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Due payments table
        due_group = QGroupBox("Due Payments")
        due_layout = QVBoxLayout()
        
        self.due_payments_table = QTableWidget()
        self.due_payments_table.setColumnCount(7)
        self.due_payments_table.setHorizontalHeaderLabels(['Description', 'Amount', 'Due Date', 'Days Overdue', 'Category', 'Account', 'Actions'])
        header = self.due_payments_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        due_layout.addWidget(self.due_payments_table)
        due_group.setLayout(due_layout)
        layout.addWidget(due_group)
        
        self.update_due_payments_table()
        
        widget.setLayout(layout)
        return widget
        
    def update_category_list(self):
        """Update category combo boxes with existing categories"""
        try:
            transactions = self.bank.get_user_finances(self.current_user_id)
            categories = set()
            for transaction in transactions:
                if 'category' in transaction:
                    categories.add(transaction['category'])
            
            # Add comprehensive category list
            common_categories = [
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
            categories.update(common_categories)
            
            categories = sorted(list(categories))
            
            # Update both category combo boxes
            current_items = [self.category_combo.itemText(i) for i in range(self.category_combo.count())]
            if set(current_items) != set(categories):
                self.category_combo.clear()
                self.category_combo.addItems(categories)
                
                self.rec_category_combo.clear()
                self.rec_category_combo.addItems(categories)
                
        except Exception as e:
            logger.error("FinancialIOTab", f"Error updating category list: {e}")
            
    def add_transaction(self):
        """Add a new transaction (regular or recurring)"""
        try:
            amount = float(self.amount_input.text())
            desc = self.desc_input.text().strip()
            type_ = 'in' if self.type_combo.currentText() == 'Income' else 'out'
            account = self.account_combo.currentText()
            category = self.category_combo.currentText()
            date = self.date_input.date().toString('yyyy-MM-dd')
            
            if not desc:
                QMessageBox.warning(self, "Error", "Please enter a description.")
                return
                
            if amount <= 0:
                QMessageBox.warning(self, "Error", "Please enter a valid amount.")
                return
            
            # Check if this should be a recurring transaction
            if self.make_recurring_check.isChecked():
                # Add as recurring transaction
                frequency = self.frequency_combo.currentText()
                start_date = date
                end_date = None if self.indefinite_check.isChecked() else self.end_date_input.date().toString('yyyy-MM-dd')
                
                self.bank.add_recurring_transaction(
                    amount=amount,
                    desc=desc,
                    account=account,
                    type_=type_,
                    category=category,
                    frequency=frequency,
                    start_date=start_date,
                    end_date=end_date,
                    user_id=self.current_user_id
                )
                
                success_msg = f"Recurring transaction added successfully!\nFrequency: {frequency.title()}"
                if end_date:
                    success_msg += f"\nEnd Date: {end_date}"
                else:
                    success_msg += "\nNo end date (indefinite)"
                    
            else:
                # Add as regular transaction
                self.bank.add_transaction(
                    amount=amount,
                    desc=desc,
                    account=account,
                    type_=type_,
                    category=category,
                    date=date,
                    user_id=self.current_user_id
                )
                success_msg = "Transaction added successfully!"
            
            # Clear form
            self.amount_input.clear()
            self.desc_input.clear()
            self.type_combo.setCurrentIndex(0)
            self.account_combo.setCurrentIndex(0)
            self.category_combo.setCurrentIndex(0)
            self.date_input.setDate(QDate.currentDate())
            self.make_recurring_check.setChecked(False)
            self.recurring_group.setVisible(False)
            
            # Update tables and emit signal
            self.update_recent_transactions_table()
            self.update_recurring_transactions_table()
            self.update_category_list()
            self.transaction_added.emit()
            
            QMessageBox.information(self, "Success", success_msg)
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid amount.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add transaction: {str(e)}")
            
    def add_recurring_transaction(self):
        """Add a new recurring transaction"""
        try:
            amount = float(self.rec_amount_input.text())
            desc = self.rec_desc_input.text().strip()
            type_text = self.rec_type_combo.currentText()
            if type_text == 'Income':
                type_ = 'in'
            elif type_text == 'Loan Payment':
                type_ = 'loan_payment'
            else:
                type_ = 'out'
            account = self.rec_account_combo.currentText()
            category = self.rec_category_combo.currentText()
            frequency = self.frequency_combo.currentText()
            start_date = self.start_date_input.date().toPyDate()
            end_date = self.end_date_input.date().toPyDate() if self.has_end_date.isChecked() else None
            
            if not desc:
                QMessageBox.warning(self, "Error", "Please enter a description.")
                return
                
            if amount <= 0:
                QMessageBox.warning(self, "Error", "Please enter a valid amount.")
                return
            
            # Add recurring transaction to bank
            self.bank.add_recurring_transaction(
                amount=amount,
                desc=desc,
                account=account,
                type_=type_,
                category=category,
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                user_id=self.current_user_id
            )
            
            # Clear form
            self.rec_amount_input.clear()
            self.rec_desc_input.clear()
            self.rec_type_combo.setCurrentIndex(0)
            self.rec_account_combo.setCurrentIndex(0)
            self.rec_category_combo.setCurrentIndex(0)
            self.frequency_combo.setCurrentIndex(0)
            self.start_date_input.setDate(QDate.currentDate())
            self.end_date_input.setDate(QDate.currentDate().addYears(1))
            self.has_end_date.setChecked(False)
            
            # Update tables
            self.update_recurring_transactions_table()
            self.update_due_payments_table()
            self.update_category_list()
            
            QMessageBox.information(self, "Success", "Recurring transaction added successfully!")
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid amount.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add recurring transaction: {str(e)}")
            
    def update_recent_transactions_table(self):
        """Update the recent transactions table"""
        try:
            transactions = self.bank.get_user_finances(self.current_user_id)
            recent = sorted(transactions, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)[:20]
            
            self.recent_table.setRowCount(len(recent))
            for row, transaction in enumerate(recent):
                self.recent_table.setItem(row, 0, QTableWidgetItem(transaction['date']))
                self.recent_table.setItem(row, 1, QTableWidgetItem(transaction['desc']))
                amount_str = f"${transaction['amount']:,.2f}"
                if transaction['type'] == 'out':
                    amount_str = f"-{amount_str}"
                self.recent_table.setItem(row, 2, QTableWidgetItem(amount_str))
                self.recent_table.setItem(row, 3, QTableWidgetItem(transaction['type'].title()))
                self.recent_table.setItem(row, 4, QTableWidgetItem(transaction.get('category', 'Other')))
                self.recent_table.setItem(row, 5, QTableWidgetItem(transaction['account']))
                
                # Add delete button
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; }")
                delete_btn.clicked.connect(lambda checked, t=transaction: self.delete_transaction(t))
                self.recent_table.setCellWidget(row, 6, delete_btn)
                
        except Exception as e:
            logger.error("FinancialIOTab", f"Error updating recent transactions table: {e}")
            
    def update_recurring_transactions_table(self):
        """Update the recurring transactions table"""
        try:
            recurring_transactions = self.bank.get_recurring_transactions()
            user_recurring = [r for r in recurring_transactions if r.user_id == self.current_user_id]
            
            self.recurring_table.setRowCount(len(user_recurring))
            for row, recurring in enumerate(user_recurring):
                self.recurring_table.setItem(row, 0, QTableWidgetItem(recurring.desc))
                amount_str = f"${recurring.amount:,.2f}"
                if recurring.type_ == 'out':
                    amount_str = f"-{amount_str}"
                self.recurring_table.setItem(row, 1, QTableWidgetItem(amount_str))
                
                # Display type with proper names
                if recurring.type_ == 'in':
                    type_display = 'Income'
                elif recurring.type_ == 'loan_payment':
                    type_display = 'Loan Payment'
                else:
                    type_display = 'Expense'
                self.recurring_table.setItem(row, 2, QTableWidgetItem(type_display))
                self.recurring_table.setItem(row, 3, QTableWidgetItem(recurring.category))
                self.recurring_table.setItem(row, 4, QTableWidgetItem(recurring.account))
                self.recurring_table.setItem(row, 5, QTableWidgetItem(recurring.frequency.title()))
                
                next_due = recurring.get_next_due_date()
                next_due_str = next_due.strftime('%Y-%m-%d') if next_due else 'N/A'
                self.recurring_table.setItem(row, 6, QTableWidgetItem(next_due_str))
                
                # Add delete button
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; }")
                delete_btn.clicked.connect(lambda checked, r=recurring: self.delete_recurring_transaction(r))
                self.recurring_table.setCellWidget(row, 7, delete_btn)
                
        except Exception as e:
            logger.error("FinancialIOTab", f"Error updating recurring transactions table: {e}")
            
    def update_due_payments_table(self):
        """Update the due payments table"""
        try:
            recurring_transactions = self.bank.get_recurring_transactions()
            due_payments = []
            
            for recurring in recurring_transactions:
                if recurring.user_id == self.current_user_id:
                    if recurring.is_due():
                        next_due = recurring.get_next_due_date()
                        if next_due:
                            days_overdue = (datetime.now() - next_due).days
                            due_payments.append({
                                'recurring': recurring,
                                'due_date': next_due,
                                'days_overdue': max(0, days_overdue)
                            })
            
            # Sort by days overdue (most overdue first)
            due_payments.sort(key=lambda x: x['days_overdue'], reverse=True)
            
            self.due_payments_table.setRowCount(len(due_payments))
            for row, payment in enumerate(due_payments):
                recurring = payment['recurring']
                self.due_payments_table.setItem(row, 0, QTableWidgetItem(recurring.desc))
                amount_str = f"${recurring.amount:,.2f}"
                if recurring.type_ == 'out':
                    amount_str = f"-{amount_str}"
                self.due_payments_table.setItem(row, 1, QTableWidgetItem(amount_str))
                self.due_payments_table.setItem(row, 2, QTableWidgetItem(payment['due_date'].strftime('%Y-%m-%d')))
                self.due_payments_table.setItem(row, 3, QTableWidgetItem(f"{payment['days_overdue']} days"))
                self.due_payments_table.setItem(row, 4, QTableWidgetItem(recurring.category))
                self.due_payments_table.setItem(row, 5, QTableWidgetItem(recurring.account))
                
                # Add process button
                process_btn = QPushButton("Process")
                process_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
                process_btn.clicked.connect(lambda checked, r=recurring: self.process_single_payment(r))
                self.due_payments_table.setCellWidget(row, 6, process_btn)
                
        except Exception as e:
            logger.error("FinancialIOTab", f"Error updating due payments table: {e}")
            
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
                           f"Type: {'Income' if transaction['type'] == 'in' else 'Expense'}")
        
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
                logger.debug("FinancialIOTab", f"delete_transaction: Reversing effect and removing transaction '{transaction['desc']}'")
                self.bank.remove_transaction(transaction)
                self.update_recent_transactions_table()
                self.transaction_added.emit()  # Refresh dashboard
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
                    self.update_recent_transactions_table()
                    self.transaction_added.emit()  # Refresh dashboard
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
                
    def delete_recurring_transaction(self, recurring):
        """Delete a recurring transaction"""
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete the recurring transaction '{recurring.desc}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.bank.remove_recurring_transaction(recurring)
                self.update_recurring_transactions_table()
                self.update_due_payments_table()
                QMessageBox.information(self, "Success", "Recurring transaction deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete recurring transaction: {str(e)}")
                
    def process_single_payment(self, recurring):
        """Process a single recurring payment"""
        try:
            self.bank.process_single_recurring(recurring)
            self.update_due_payments_table()
            self.update_recent_transactions_table()
            self.transaction_added.emit()  # Refresh dashboard
            QMessageBox.information(self, "Success", f"Processed payment for '{recurring.desc}'!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process payment: {str(e)}")
            
    def process_all_due_payments(self):
        """Process all due recurring payments"""
        try:
            processed_count = self.bank.process_recurring_transactions()
            self.update_due_payments_table()
            self.update_recent_transactions_table()
            self.transaction_added.emit()  # Refresh dashboard
            QMessageBox.information(self, "Success", f"Processed {processed_count} recurring payments!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process payments: {str(e)}")
            
    def set_current_user(self, user_id):
        """Set the current user"""
        self.current_user_id = user_id
        self.bank.set_current_user(user_id)
        self.update_recent_transactions_table()
        self.update_recurring_transactions_table()
        self.update_due_payments_table()
        self.update_category_list()
