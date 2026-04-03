from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QComboBox, QLineEdit, QPushButton, QMessageBox, QDateEdit, QTextEdit, QInputDialog
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from assets.Logger import Logger
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
try:
    from src.settings import SettingsController
except ImportError:
    from settings import SettingsController

logger = Logger()

class PaymentDialog(QDialog):
    def __init__(self, parent=None, mode='add', payment_data=None, tenant=None):
        super().__init__(parent)
        logger.debug("PaymentDialog", f"Initializing PaymentDialog in {mode} mode")
        self.mode = mode  # 'add', 'modify', or 'refund'
        self.payment_data = payment_data
        self.delete_requested = False
        self.tenant = tenant  # Store tenant for overpayment credit access
        try:
            self.settings = SettingsController()
        except Exception:
            self.settings = None
        
        if mode == 'refund':
            title = 'Refund/Reverse Payment'
        elif mode == 'add':
            title = 'Add Payment'
        else:
            title = 'Modify Payment'
        
        self.setWindowTitle(title)
        self.setFixedSize(500, 400)
        self.init_ui()
        
        if mode == 'modify' and payment_data:
            self.load_payment_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        if self.mode == 'refund':
            title_text = 'Refund/Reverse Payment'
            title_color = '#dc3545'  # Red for refunds
        elif self.mode == 'add':
            title_text = 'Add New Payment'
            title_color = '#0056b3'
        else:
            title_text = 'Modify Payment'
            title_color = '#0056b3'
        
        title = QLabel(title_text)
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {title_color}; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Add explanation for refund mode
        if self.mode == 'refund':
            refund_info = QLabel('Record a refund or money returned to the tenant.\nThis will be recorded as a negative payment.')
            refund_info.setStyleSheet("""color: #721c24; 
                background-color: #f8d7da; 
                padding: 8px; 
                border: 1px solid #f5c6cb; 
                border-radius: 4px;
                font-size: 12px;""")
            refund_info.setWordWrap(True)
            layout.addWidget(refund_info)
        
        # Amount section
        amount_layout = QHBoxLayout()
        amount_label = QLabel('Amount:')
        amount_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(100000)
        # Allow negative amounts in modify mode (for refund modifications)
        if self.mode == 'modify':
            self.amount_input.setMinimum(-100000)
        else:
            self.amount_input.setMinimum(0)
        self.amount_input.setPrefix('$')
        self.amount_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount_input)
        layout.addLayout(amount_layout)
        
        # Payment type section
        type_layout = QHBoxLayout()
        type_label = QLabel('Payment Type:')
        type_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(self._get_payment_types())
        self.type_combo.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        
        add_type_btn = QPushButton('+')
        add_type_btn.setFixedSize(30, 30)
        add_type_btn.setToolTip('Add a custom payment type')
        add_type_btn.clicked.connect(self.add_custom_type)
        add_type_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d; color: white; border: none;
                border-radius: 4px; font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5a6268; }
        """)

        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addWidget(add_type_btn)
        layout.addLayout(type_layout)
        
        # Disable credit options in refund mode (can't refund credits)
        if self.mode == 'refund':
            # Remove credit-based payment types for refunds
            credit_index = self.type_combo.findText('Overpayment Credit')
            if credit_index >= 0:
                self.type_combo.removeItem(credit_index)
            service_index = self.type_combo.findText('Service Credit')
            if service_index >= 0:
                self.type_combo.removeItem(service_index)
        
        # Overpayment credit info (hidden by default)
        self.credit_info_layout = QHBoxLayout()
        self.credit_info_label = QLabel()
        self.credit_info_label.setStyleSheet("""
            color: #28a745; 
            font-weight: bold; 
            background-color: #d4edda; 
            padding: 8px; 
            border: 1px solid #c3e6cb; 
            border-radius: 4px;
        """)
        self.credit_info_label.hide()
        self.credit_info_layout.addWidget(self.credit_info_label)
        layout.addLayout(self.credit_info_layout)
        
        # Other payment type input (hidden by default)
        other_layout = QHBoxLayout()
        other_label = QLabel('Specify Type:')
        other_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.other_input = QLineEdit()
        self.other_input.setPlaceholderText("Enter payment type...")
        self.other_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.other_input.hide()
        
        other_layout.addWidget(other_label)
        other_layout.addWidget(self.other_input)
        self.other_layout = other_layout
        layout.addLayout(other_layout)
        
        # Payment month selection
        month_layout = QHBoxLayout()
        month_label = QLabel('Payment For:')
        month_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.month_combo = QComboBox()
        self.month_combo.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        # Populate with smart month selection
        self.populate_smart_months()
        
        # Set current month as default
        self.month_combo.setCurrentIndex(0)
        
        month_layout.addWidget(month_label)
        month_layout.addWidget(self.month_combo)
        layout.addLayout(month_layout)
        
        # Payment received date
        date_layout = QHBoxLayout()
        date_label = QLabel('Date Received:')
        date_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.date_received = QDateEdit()
        self.date_received.setDate(QDate.currentDate())
        self.date_received.setCalendarPopup(True)
        self.date_received.setMinimumWidth(200)  # Ensure calendar popup is not cut off
        self.date_received.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        # Set calendar widget properties when shown
        calendar = self.date_received.calendarWidget()
        if calendar:
            calendar.setMinimumSize(300, 200)  # Ensure calendar is large enough
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_received)
        layout.addLayout(date_layout)
        
        # Notes section (optional)
        notes_layout = QVBoxLayout()
        notes_label = QLabel('Notes (Optional):')
        notes_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Add any additional notes about this payment/refund...")
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.notes_input)
        layout.addLayout(notes_layout)
        
        # Spacer
        layout.addStretch()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        # Add/Update button
        if self.mode == 'refund':
            button_text = 'Record Refund'
            button_color = '#dc3545'
            button_hover = '#c82333'
            button_pressed = '#bd2130'
        elif self.mode == 'add':
            button_text = 'Add Payment'
            button_color = '#28a745'
            button_hover = '#218838'
            button_pressed = '#1e7e34'
        else:
            button_text = 'Update Payment'
            button_color = '#28a745'
            button_hover = '#218838'
            button_pressed = '#1e7e34'
        
        self.action_btn = QPushButton(button_text)
        self.action_btn.clicked.connect(self.accept)
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_color};
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QPushButton:pressed {{
                background-color: {button_pressed};
            }}
        """)
        
        # Cancel button
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
            QPushButton:pressed {
                background-color: #494f54;
            }
        """)
        
        buttons_layout.addWidget(self.action_btn)
        buttons_layout.addWidget(cancel_btn)
        
        # Delete button (only for modify mode)
        if self.mode == 'modify':
            delete_btn = QPushButton('Delete Payment')
            delete_btn.clicked.connect(self.delete_payment)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
            buttons_layout.addWidget(delete_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def on_type_changed(self, text):
        """Show/hide appropriate input fields based on payment type"""
        print(f"[DEBUG] on_type_changed - current amount: {self.amount_input.value()}, new type: {text}")
        if text == 'Other':
            self.other_input.show()
            self.credit_info_label.hide()
        elif text == 'Overpayment Credit':
            self.other_input.hide()
            # Show available overpayment credit
            if self.tenant and hasattr(self.tenant, 'overpayment_credit'):
                available_credit = getattr(self.tenant, 'overpayment_credit', 0.0)
                self.credit_info_label.setText(f"Available Overpayment Credit: ${available_credit:.2f}")
                self.credit_info_label.show()
                
                # Set maximum amount to available credit
                print(f"[DEBUG] Setting max amount to: {available_credit}")
                self.amount_input.setMaximum(available_credit)
                if available_credit > 0:
                    new_value = min(self.amount_input.value(), available_credit)
                    print(f"[DEBUG] Setting amount to min of current ({self.amount_input.value()}) and available ({available_credit}): {new_value}")
                    self.amount_input.setValue(new_value)
                else:
                    self.amount_input.setValue(0)
                    self.credit_info_label.setText("No overpayment credit available")
                    self.credit_info_label.setStyleSheet("""
                        color: #721c24; 
                        font-weight: bold; 
                        background-color: #f8d7da; 
                        padding: 8px; 
                        border: 1px solid #f5c6cb; 
                        border-radius: 4px;
                    """)
            else:
                self.credit_info_label.setText("No overpayment credit available")
                self.credit_info_label.show()
        elif text == 'Service Credit':
            self.other_input.hide()
            # Show available service credit
            if self.tenant and hasattr(self.tenant, 'service_credit'):
                available_credit = getattr(self.tenant, 'service_credit', 0.0)
                self.credit_info_label.setText(f"Available Service Credit: ${available_credit:.2f}")
                self.credit_info_label.show()
                
                # Set maximum amount to available credit
                self.amount_input.setMaximum(available_credit)
                if available_credit > 0:
                    self.amount_input.setValue(min(self.amount_input.value(), available_credit))
                else:
                    self.amount_input.setValue(0)
                    self.credit_info_label.setText("No service credit available")
                    self.credit_info_label.setStyleSheet("""
                        color: #721c24; 
                        font-weight: bold; 
                        background-color: #f8d7da; 
                        padding: 8px; 
                        border: 1px solid #f5c6cb; 
                        border-radius: 4px;
                    """)
            else:
                self.credit_info_label.setText("No service credit available")
                self.credit_info_label.show()
        else:
            self.other_input.hide()
            self.credit_info_label.hide()
            # Reset amount input maximum for other payment types
            self.amount_input.setMaximum(999999.99)
    
    def _get_payment_types(self):
        """Load payment types from settings, fall back to defaults."""
        if self.settings:
            try:
                return self.settings.get_payment_types()
            except Exception:
                pass
        return ['Cash', 'Bilt', 'Zelle', 'Bank Transfer', 'Check', 'Venmo',
                'Overpayment Credit', 'Service Credit', 'Other']

    def add_custom_type(self):
        """Prompt the user to add a new payment type and persist it to settings."""
        text, ok = QInputDialog.getText(
            self, 'Add Payment Type', 'New payment type name:',
            text=''
        )
        if not ok or not text.strip():
            return
        type_name = text.strip()
        if self.settings:
            added = self.settings.add_payment_type(type_name)
        else:
            added = True  # No settings available; just add to combo for this session
        if added:
            other_idx = self.type_combo.findText('Other')
            if other_idx >= 0:
                self.type_combo.insertItem(other_idx, type_name)
            else:
                self.type_combo.addItem(type_name)
            self.type_combo.setCurrentText(type_name)
        else:
            QMessageBox.information(self, 'Already Exists',
                                    f'"{type_name}" is already in the payment types list.')

    def populate_smart_months(self):
        """Populate month dropdown with intelligent selection based on rental period"""
        self.month_combo.clear()
        
        if not self.tenant or not hasattr(self.tenant, 'months_to_charge') or not self.tenant.months_to_charge:
            # Fallback to basic month selection if no tenant or rental period info
            self.populate_fallback_months()
            return
        
        from datetime import date
        today = date.today()
        current_month = (today.year, today.month)
        
        # Get all months in rental period
        rental_months = [(year, month) for year, month in self.tenant.months_to_charge]
        rental_months.sort()
        
        # Check which months are fully paid
        paid_months = []
        unpaid_months = []
        past_months = []
        available_months = []
        
        for year, month in rental_months:
            # Calculate total payments for this month
            total_paid = 0
            if hasattr(self.tenant, 'payment_history'):
                for payment in self.tenant.payment_history:
                    # Check payment_month field (format: YYYY-MM)
                    payment_month = payment.get('payment_month', '')
                    if payment_month == f"{year}-{month:02d}":
                        total_paid += payment.get('amount', 0)
            
            # Get expected rent for this month
            expected_rent = 0
            try:
                # We need access to rent_tracker for get_effective_rent
                if hasattr(self.parent(), 'rent_tracker'):
                    expected_rent = self.parent().rent_tracker.get_effective_rent(self.tenant, year, month)
                else:
                    expected_rent = getattr(self.tenant, 'rent_amount', 0)
            except:
                expected_rent = getattr(self.tenant, 'rent_amount', 0)
            
            month_tuple = (year, month)
            is_fully_paid = total_paid >= expected_rent
            is_past = month_tuple < current_month
            
            # Add month info
            month_info = {
                'year': year,
                'month': month,
                'total_paid': total_paid,
                'expected': expected_rent,
                'is_fully_paid': is_fully_paid,
                'is_past': is_past,
                'is_current': month_tuple == current_month
            }
            
            available_months.append(month_info)
            
            # Categorize months
            if is_past:
                past_months.append(month_info)
            elif is_fully_paid:
                paid_months.append(month_info)
            else:
                unpaid_months.append(month_info)
        
        # Sort each category by date
        past_months.sort(key=lambda x: (x['year'], x['month']), reverse=True)  # Most recent first
        unpaid_months.sort(key=lambda x: (x['year'], x['month']))
        paid_months.sort(key=lambda x: (x['year'], x['month']))
        
        # Combine in priority order:
        # 1. Current month (if unpaid)
        # 2. Future unpaid months
        # 3. Paid months (current and future)
        # 4. Past unpaid months (reversed so most recent first)
        # 5. Past paid months (reversed so most recent first)
        
        current_month_info = [m for m in available_months if m['is_current']]
        future_unpaid = [m for m in unpaid_months if not m['is_past'] and not m['is_current']]
        future_paid = [m for m in paid_months if not m['is_past']]
        past_unpaid = [m for m in past_months if not m['is_fully_paid']]
        past_paid = [m for m in past_months if m['is_fully_paid']]
        
        ordered_months = current_month_info + future_unpaid + future_paid + past_unpaid + past_paid
        
        # Add months to dropdown
        for month_info in ordered_months:
            year, month = month_info['year'], month_info['month']
            month_date = date(year, month, 1)
            
            # Create display text with status
            month_str = month_date.strftime('%B %Y')
            status = ""
            if month_info['is_fully_paid']:
                status = " (Paid)"
            elif month_info['total_paid'] > 0:
                status = f" (${month_info['total_paid']:.0f}/${month_info['expected']:.0f})"
            elif month_info['is_past']:
                status = f" (${month_info['expected']:.0f} due)"
            else:
                status = f" (${month_info['expected']:.0f} due)"
            
            display_text = f"{month_str}{status}"
            value = f"{year}-{month:02d}"
            
            self.month_combo.addItem(display_text, value)
    
    def populate_fallback_months(self):
        """Fallback month population when no rental period info available"""
        current_date = datetime.now()
        for i in range(12):  # Show last 12 months
            month_date = datetime(current_date.year, current_date.month, 1)
            if i > 0:
                # Go back in months
                if month_date.month == 1:
                    month_date = month_date.replace(year=month_date.year - 1, month=12)
                else:
                    month_date = month_date.replace(month=month_date.month - 1)
                current_date = month_date
            
            month_str = month_date.strftime('%Y-%m (%B %Y)')
            month_value = month_date.strftime('%Y-%m')
            self.month_combo.addItem(month_str, month_value)
    
    def load_payment_data(self):
        """Load existing payment data for modification"""
        if self.payment_data:
            # Load actual payment data if available
            if isinstance(self.payment_data, dict):
                self.amount_input.setValue(self.payment_data.get('amount', 0.0))
                
                payment_type = self.payment_data.get('type', 'Cash')
                # Handle "Other: ..." format
                if payment_type.startswith('Other:'):
                    self.type_combo.setCurrentText('Other')
                    self.other_input.setText(payment_type[7:].strip())  # Remove "Other: " prefix
                    self.other_input.show()
                else:
                    self.type_combo.setCurrentText(payment_type)
                
                # Set payment month if available
                payment_month = self.payment_data.get('payment_month', '')
                if payment_month:
                    for i in range(self.month_combo.count()):
                        if self.month_combo.itemData(i) == payment_month:
                            self.month_combo.setCurrentIndex(i)
                
                # Load notes if available
                notes = self.payment_data.get('notes', '')
                if notes and hasattr(self, 'notes_input'):
                    self.notes_input.setPlainText(notes)
                
                # Set received date if available
                date_received = self.payment_data.get('date', '')
                if date_received:
                    try:
                        date_obj = datetime.strptime(date_received, '%Y-%m-%d')
                        self.date_received.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
                    except ValueError:
                        pass  # Keep default current date
                
                # Set date range restrictions based on rental period
                self.set_date_range_from_rental_period()
            else:
                # Fallback for old format
                self.amount_input.setValue(1600.0)  # Default rent amount
                self.type_combo.setCurrentText('Cash')  # Default type
    
    def set_date_range_from_rental_period(self):
        """Set the date picker range based on the tenant's rental period"""
        if not self.tenant or not hasattr(self.tenant, 'rental_period'):
            return
        
        rental_period = self.tenant.rental_period
        if not rental_period:
            return
        
        try:
            # Get start and end dates from rental period
            start_date_str = rental_period.get('start_date') if isinstance(rental_period, dict) else None
            end_date_str = rental_period.get('end_date') if isinstance(rental_period, dict) else None
            
            if start_date_str and end_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                # Set date range on the date edit widget
                self.date_received.setMinimumDate(QDate(start_date.year, start_date.month, start_date.day))
                self.date_received.setMaximumDate(QDate(end_date.year, end_date.month, end_date.day))
        except (ValueError, AttributeError, TypeError):
            # If rental period format is invalid, allow any date
            pass
    
    def delete_payment(self):
        """Handle delete payment request"""
        reply = QMessageBox.question(self, "Delete Payment", 
            f"Are you sure you want to delete this payment?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested = True
            logger.debug("PaymentDialog", "delete_requested set to True, accepting dialog")
            # Call parent's accept to properly close with Accepted status
            super().accept()
    
    def accept(self):
        """Validate and accept the dialog"""
        # Skip validation if we're deleting
        if self.delete_requested:
            logger.debug("PaymentDialog", "Skipping validation because delete_requested is True")
            super().accept()
            return
        
        amount = self.amount_input.value()
        # Allow negative amounts in modify mode (for refund modifications)
        # In refund mode, amount should be positive (will be negated later)
        # In add mode, amount must be positive
        if self.mode == 'refund' and amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid refund amount (positive value).")
            return
        elif self.mode == 'add' and amount <= 0:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid payment amount (positive value).")
            return
        elif self.mode == 'modify' and amount == 0:
            QMessageBox.warning(self, "Invalid Amount", "Amount cannot be zero.")
            return
        
        payment_type = self.type_combo.currentText()
        if payment_type == 'Other':
            other_type = self.other_input.text().strip()
            if not other_type:
                QMessageBox.warning(self, "Invalid Payment Type", "Please specify the payment type for 'Other'.")
                return
        
        super().accept()
    
    def get_payment_data(self):
        """Get the payment data from the dialog"""
        amount = self.amount_input.value()
        payment_type = self.type_combo.currentText()
        
        logger.debug("PaymentDialog", f"[DEBUG] get_payment_data - amount: {amount}, type: {payment_type}")
        
        if payment_type == 'Other':
            other_type = self.other_input.text().strip()
            payment_type = f"Other: {other_type}"
        
        # Get the selected month
        payment_month = self.month_combo.currentData()  # This returns the YYYY-MM format
        
        # Get the received date
        date_received = self.date_received.date().toString('yyyy-MM-dd')
        
        # Get notes (optional)
        notes = self.notes_input.toPlainText().strip() if hasattr(self, 'notes_input') else ''
        
        return {
            'amount': amount,
            'payment_type': payment_type,
            'payment_month': payment_month,
            'date_received': date_received,
            'notes': notes
        }
