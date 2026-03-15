from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QComboBox, QPushButton, 
                             QDateEdit, QSpinBox, QGroupBox, QMessageBox, QFrame,
                             QScrollArea, QWidget, QCheckBox, QDoubleSpinBox,
                             QGridLayout, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime, date
from assets.Logger import Logger

logger = Logger()

class TenantDetailsDialog(QDialog):
    """Dialog for editing comprehensive tenant details including notification preferences"""
    
    tenant_updated = pyqtSignal()  # Signal emitted when tenant details are updated
    
    def __init__(self, parent=None, tenant=None, rent_tracker=None):
        super().__init__(parent)
        logger.debug("TenantDetailsDialog", f"Initializing TenantDetailsDialog for tenant {tenant.name if tenant else 'Unknown'}")
        self.tenant = tenant
        self.rent_tracker = rent_tracker
        
        self.setWindowTitle(f'Edit Tenant Details - {tenant.name if tenant else "New Tenant"}')
        self.setFixedSize(800, 700)
        self.init_ui()
        
        if tenant:
            self.load_tenant_data()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel(f'Tenant Details - {self.tenant.name if self.tenant else "New Tenant"}')
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0056b3; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Basic Information Tab
        self.basic_tab = self.create_basic_info_tab()
        tab_widget.addTab(self.basic_tab, "Basic Information")
        
        # Contact Information Tab
        self.contact_tab = self.create_contact_info_tab()
        tab_widget.addTab(self.contact_tab, "Contact Information")
        
        # Notification Preferences Tab
        self.notification_tab = self.create_notification_preferences_tab()
        tab_widget.addTab(self.notification_tab, "Notification Preferences")
        
        # Lease Information Tab
        self.lease_tab = self.create_lease_info_tab()
        tab_widget.addTab(self.lease_tab, "Lease Information")
        
        main_layout.addWidget(tab_widget)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton('Save Changes')
        save_btn.clicked.connect(self.save_changes)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
    
    def create_basic_info_tab(self):
        """Create basic information tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QGridLayout()
        
        # Name
        basic_layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_edit = QLineEdit()
        basic_layout.addWidget(self.name_edit, 0, 1)
        
        # Tenant ID
        basic_layout.addWidget(QLabel("Tenant ID:"), 1, 0)
        self.tenant_id_edit = QLineEdit()
        self.tenant_id_edit.setReadOnly(True)  # ID shouldn't be editable
        basic_layout.addWidget(self.tenant_id_edit, 1, 1)
        
        # Notes
        basic_layout.addWidget(QLabel("Notes:"), 2, 0)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        basic_layout.addWidget(self.notes_edit, 2, 1)
        
        # Account Status
        basic_layout.addWidget(QLabel("Account Status:"), 3, 0)
        self.status_combo = QComboBox()
        self.status_combo.addItems(['active', 'inactive', 'suspended', 'terminated'])
        basic_layout.addWidget(self.status_combo, 3, 1)
        
        basic_group.setLayout(basic_layout)
        scroll_layout.addWidget(basic_group)
        
        # Financial Information Group
        financial_group = QGroupBox("Financial Information")
        financial_layout = QGridLayout()
        
        # Rent Amount
        financial_layout.addWidget(QLabel("Rent Amount:"), 0, 0)
        self.rent_amount_spin = QDoubleSpinBox()
        self.rent_amount_spin.setRange(0, 99999)
        self.rent_amount_spin.setPrefix("$")
        financial_layout.addWidget(self.rent_amount_spin, 0, 1)
        
        # Deposit Amount
        financial_layout.addWidget(QLabel("Deposit Amount:"), 1, 0)
        self.deposit_amount_spin = QDoubleSpinBox()
        self.deposit_amount_spin.setRange(0, 99999)
        self.deposit_amount_spin.setPrefix("$")
        financial_layout.addWidget(self.deposit_amount_spin, 1, 1)
        
        # Due Day
        financial_layout.addWidget(QLabel("Due Day:"), 2, 0)
        self.due_day_spin = QSpinBox()
        self.due_day_spin.setRange(1, 31)
        financial_layout.addWidget(self.due_day_spin, 2, 1)
        
        # Delinquency Balance
        financial_layout.addWidget(QLabel("Delinquency Balance:"), 3, 0)
        self.delinquency_balance_spin = QDoubleSpinBox()
        self.delinquency_balance_spin.setRange(-99999, 99999)
        self.delinquency_balance_spin.setPrefix("$")
        financial_layout.addWidget(self.delinquency_balance_spin, 3, 1)
        
        # Overpayment Credit
        financial_layout.addWidget(QLabel("Overpayment Credit:"), 4, 0)
        self.overpayment_credit_spin = QDoubleSpinBox()
        self.overpayment_credit_spin.setRange(-99999, 99999)
        self.overpayment_credit_spin.setPrefix("$")
        financial_layout.addWidget(self.overpayment_credit_spin, 4, 1)
        
        financial_group.setLayout(financial_layout)
        scroll_layout.addWidget(financial_group)
        
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        return widget
    
    def create_contact_info_tab(self):
        """Create contact information tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Contact Information Group
        contact_group = QGroupBox("Contact Information")
        contact_layout = QGridLayout()
        
        # Phone
        contact_layout.addWidget(QLabel("Phone:"), 0, 0)
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("(555) 123-4567")
        contact_layout.addWidget(self.phone_edit, 0, 1)
        
        # Email
        contact_layout.addWidget(QLabel("Email:"), 1, 0)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("tenant@example.com")
        contact_layout.addWidget(self.email_edit, 1, 1)
        
        # Legacy Contact (for backward compatibility)
        contact_layout.addWidget(QLabel("Legacy Contact:"), 2, 0)
        self.legacy_contact_edit = QLineEdit()
        self.legacy_contact_edit.setPlaceholderText("Additional contact information")
        contact_layout.addWidget(self.legacy_contact_edit, 2, 1)
        
        # Emergency Contact
        contact_layout.addWidget(QLabel("Emergency Contact:"), 3, 0)
        self.emergency_contact_edit = QTextEdit()
        self.emergency_contact_edit.setMaximumHeight(80)
        self.emergency_contact_edit.setPlaceholderText("Emergency contact name and phone number")
        contact_layout.addWidget(self.emergency_contact_edit, 3, 1)
        
        contact_group.setLayout(contact_layout)
        layout.addWidget(contact_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_notification_preferences_tab(self):
        """Create notification preferences tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Notification Preferences Group
        pref_group = QGroupBox("Notification Preferences")
        pref_layout = QVBoxLayout()
        
        # Notification Methods
        methods_label = QLabel("Preferred Notification Methods:")
        methods_label.setStyleSheet("font-weight: bold;")
        pref_layout.addWidget(methods_label)
        
        methods_layout = QHBoxLayout()
        self.notify_system_check = QCheckBox("System Notifications")
        self.notify_email_check = QCheckBox("Email Notifications")
        self.notify_sms_check = QCheckBox("SMS Notifications")
        
        methods_layout.addWidget(self.notify_system_check)
        methods_layout.addWidget(self.notify_email_check)
        methods_layout.addWidget(self.notify_sms_check)
        pref_layout.addLayout(methods_layout)
        
        # Notification Types
        types_label = QLabel("Notification Types to Send:")
        types_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        pref_layout.addWidget(types_label)
        
        self.notify_rent_due_check = QCheckBox("Rent Due Reminders")
        self.notify_payment_overdue_check = QCheckBox("Payment Overdue Notices")
        self.notify_lease_expiry_check = QCheckBox("Lease Expiry Warnings")
        self.notify_maintenance_check = QCheckBox("Maintenance Reminders")
        self.notify_general_check = QCheckBox("General Notifications")
        
        pref_layout.addWidget(self.notify_rent_due_check)
        pref_layout.addWidget(self.notify_payment_overdue_check)
        pref_layout.addWidget(self.notify_lease_expiry_check)
        pref_layout.addWidget(self.notify_maintenance_check)
        pref_layout.addWidget(self.notify_general_check)
        
        pref_group.setLayout(pref_layout)
        scroll_layout.addWidget(pref_group)
        
        # Timing Preferences Group
        timing_group = QGroupBox("Notification Timing")
        timing_layout = QGridLayout()
        
        # Rent reminder advance days
        timing_layout.addWidget(QLabel("Rent Due Reminder (days before):"), 0, 0)
        self.rent_reminder_days_spin = QSpinBox()
        self.rent_reminder_days_spin.setRange(0, 30)
        self.rent_reminder_days_spin.setValue(3)  # Default 3 days
        timing_layout.addWidget(self.rent_reminder_days_spin, 0, 1)
        
        # Overdue notice delay
        timing_layout.addWidget(QLabel("Overdue Notice (days after due):"), 1, 0)
        self.overdue_notice_days_spin = QSpinBox()
        self.overdue_notice_days_spin.setRange(0, 30)
        self.overdue_notice_days_spin.setValue(1)  # Default 1 day
        timing_layout.addWidget(self.overdue_notice_days_spin, 1, 1)
        
        # Lease expiry warning
        timing_layout.addWidget(QLabel("Lease Expiry Warning (days before):"), 2, 0)
        self.lease_expiry_days_spin = QSpinBox()
        self.lease_expiry_days_spin.setRange(0, 365)
        self.lease_expiry_days_spin.setValue(30)  # Default 30 days
        timing_layout.addWidget(self.lease_expiry_days_spin, 2, 1)
        
        timing_group.setLayout(timing_layout)
        scroll_layout.addWidget(timing_group)
        
        # Custom Message Templates Group
        templates_group = QGroupBox("Custom Message Templates")
        templates_layout = QVBoxLayout()
        
        # Rent due template
        templates_layout.addWidget(QLabel("Rent Due Template:"))
        self.rent_due_template_edit = QTextEdit()
        self.rent_due_template_edit.setMaximumHeight(60)
        self.rent_due_template_edit.setPlaceholderText("Your rent payment of ${amount} is due on {due_date}.")
        templates_layout.addWidget(self.rent_due_template_edit)
        
        # Overdue template
        templates_layout.addWidget(QLabel("Payment Overdue Template:"))
        self.overdue_template_edit = QTextEdit()
        self.overdue_template_edit.setMaximumHeight(60)
        self.overdue_template_edit.setPlaceholderText("Your rent payment of ${amount} is overdue. Please pay immediately.")
        templates_layout.addWidget(self.overdue_template_edit)
        
        templates_group.setLayout(templates_layout)
        scroll_layout.addWidget(templates_group)
        
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        return widget
    
    def create_lease_info_tab(self):
        """Create lease information tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Lease Information Group
        lease_group = QGroupBox("Lease Information")
        lease_layout = QGridLayout()
        
        # Rental Period Start
        lease_layout.addWidget(QLabel("Lease Start Date:"), 0, 0)
        self.lease_start_date = QDateEdit()
        self.lease_start_date.setCalendarPopup(True)
        self.lease_start_date.setDate(QDate.currentDate())
        self.lease_start_date.setMinimumWidth(200)
        calendar = self.lease_start_date.calendarWidget()
        if calendar:
            calendar.setMinimumSize(300, 200)
        self.lease_start_date.dateChanged.connect(self.validate_lease_dates)
        lease_layout.addWidget(self.lease_start_date, 0, 1)
        
        # Rental Period End
        lease_layout.addWidget(QLabel("Lease End Date:"), 1, 0)
        self.lease_end_date = QDateEdit()
        self.lease_end_date.setCalendarPopup(True)
        self.lease_end_date.setDate(QDate.currentDate().addYears(1))
        self.lease_end_date.setMinimumWidth(200)
        calendar = self.lease_end_date.calendarWidget()
        if calendar:
            calendar.setMinimumSize(300, 200)
        self.lease_end_date.dateChanged.connect(self.validate_lease_dates)
        lease_layout.addWidget(self.lease_end_date, 1, 1)
        
        # Add validation status label
        self.date_validation_label = QLabel("")
        self.date_validation_label.setStyleSheet("color: red; font-weight: bold; font-size: 11px;")
        self.date_validation_label.setWordWrap(True)
        lease_layout.addWidget(self.date_validation_label, 3, 0, 1, 2)
        
        # Lease Type
        lease_layout.addWidget(QLabel("Lease Type:"), 4, 0)
        self.lease_type_combo = QComboBox()
        self.lease_type_combo.addItems(['Fixed Term', 'Month-to-Month', 'Week-to-Week', 'Other'])
        lease_layout.addWidget(self.lease_type_combo, 4, 1)
        
        lease_group.setLayout(lease_layout)
        layout.addWidget(lease_group)
        
        widget.setLayout(layout)
        return widget
    
    def load_tenant_data(self):
        """Load existing tenant data into the form"""
        if not self.tenant:
            return
        
        # Basic Information
        self.name_edit.setText(self.tenant.name or "")
        self.tenant_id_edit.setText(self.tenant.tenant_id or "")
        self.notes_edit.setPlainText(self.tenant.notes or "")
        
        # Set status (normalize to lowercase for matching)
        status = (self.tenant.account_status or "active").lower()
        index = self.status_combo.findText(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
        
        # Financial Information
        self.rent_amount_spin.setValue(self.tenant.rent_amount or 0)
        self.deposit_amount_spin.setValue(self.tenant.deposit_amount or 0)
        self.due_day_spin.setValue(self.tenant.due_day or 1)
        self.delinquency_balance_spin.setValue(self.tenant.delinquency_balance or 0)
        self.overpayment_credit_spin.setValue(self.tenant.overpayment_credit or 0)
        
        # Contact Information
        contact_info = self.tenant.contact_info or {}
        if isinstance(contact_info, dict):
            self.phone_edit.setText(contact_info.get('phone', ''))
            self.email_edit.setText(contact_info.get('email', ''))
            self.legacy_contact_edit.setText(contact_info.get('contact', ''))
            self.emergency_contact_edit.setPlainText(contact_info.get('emergency_contact', ''))
        else:
            # Legacy string contact field
            self.legacy_contact_edit.setText(str(contact_info))
        
        # Notification Preferences
        notification_prefs = getattr(self.tenant, 'notification_preferences', {})
        
        # Notification methods
        methods = notification_prefs.get('methods', ['system'])
        self.notify_system_check.setChecked('system' in methods)
        self.notify_email_check.setChecked('email' in methods)
        self.notify_sms_check.setChecked('sms' in methods)
        
        # Notification types
        types = notification_prefs.get('types', ['rent_due', 'payment_overdue', 'lease_expiry'])
        self.notify_rent_due_check.setChecked('rent_due' in types)
        self.notify_payment_overdue_check.setChecked('payment_overdue' in types)
        self.notify_lease_expiry_check.setChecked('lease_expiry' in types)
        self.notify_maintenance_check.setChecked('maintenance' in types)
        self.notify_general_check.setChecked('general' in types)
        
        # Timing preferences
        timing = notification_prefs.get('timing', {})
        self.rent_reminder_days_spin.setValue(timing.get('rent_reminder_days', 3))
        self.overdue_notice_days_spin.setValue(timing.get('overdue_notice_days', 1))
        self.lease_expiry_days_spin.setValue(timing.get('lease_expiry_days', 30))
        
        # Message templates
        templates = notification_prefs.get('templates', {})
        self.rent_due_template_edit.setPlainText(templates.get('rent_due', ''))
        self.overdue_template_edit.setPlainText(templates.get('overdue', ''))
        
        # Lease Information
        rental_period = getattr(self.tenant, 'rental_period', {})
        if isinstance(rental_period, dict):
            start_date = rental_period.get('start_date')
            end_date = rental_period.get('end_date')
        elif isinstance(rental_period, (list, tuple)) and len(rental_period) >= 2:
            # Handle legacy format [start_date, end_date]
            start_date = rental_period[0]
            end_date = rental_period[1]
        else:
            start_date = None
            end_date = None
            
        if start_date:
            try:
                start_qdate = QDate.fromString(start_date, 'yyyy-MM-dd')
                self.lease_start_date.setDate(start_qdate)
            except:
                pass
        
        if end_date:
            try:
                end_qdate = QDate.fromString(end_date, 'yyyy-MM-dd')
                self.lease_end_date.setDate(end_qdate)
            except:
                pass
        
        # Initial validation of dates
        self.validate_lease_dates()
    
    def validate_lease_dates(self):
        """Validate that lease end date is after start date"""
        start_date = self.lease_start_date.date()
        end_date = self.lease_end_date.date()
        
        if end_date <= start_date:
            self.date_validation_label.setText("⚠ End date must be after start date")
            self.date_validation_label.setStyleSheet("color: red; font-weight: bold; font-size: 11px;")
            return False
        else:
            # Calculate lease duration for display
            days_diff = start_date.daysTo(end_date)
            years = days_diff // 365
            months = (days_diff % 365) // 30
            
            if years > 0:
                duration_text = f"✓ Valid lease duration: {years} year(s)"
                if months > 0:
                    duration_text += f" and {months} month(s)"
            elif months > 0:
                duration_text = f"✓ Valid lease duration: {months} month(s)"
            else:
                duration_text = f"✓ Valid lease duration: {days_diff} day(s)"
                
            self.date_validation_label.setText(duration_text)
            self.date_validation_label.setStyleSheet("color: green; font-weight: bold; font-size: 11px;")
            return True
    
    def save_changes(self):
        """Save changes to the tenant"""
        if not self.tenant or not self.rent_tracker:
            QMessageBox.warning(self, "Error", "No tenant or rent tracker available.")
            return
        
        # Validate lease dates before saving
        if not self.validate_lease_dates():
            QMessageBox.warning(self, "Invalid Dates", 
                              "Cannot save: Lease end date must be after start date.")
            return
        
        try:
            # Track changes for automatic notes
            changes = []
            original_rental_period = getattr(self.tenant, 'rental_period', {})
            
            # Check for significant changes that need notes
            if self.tenant.name != self.name_edit.text().strip():
                old_name = self.tenant.name
                new_name = self.name_edit.text().strip()
                changes.append(f"Name changed from '{old_name}' to '{new_name}'")
            
            if self.tenant.rent_amount != self.rent_amount_spin.value():
                old_rent = self.tenant.rent_amount
                new_rent = self.rent_amount_spin.value()
                changes.append(f"Rent amount changed from ${old_rent:.2f} to ${new_rent:.2f}")
            
            if self.tenant.due_day != self.due_day_spin.value():
                old_due = self.tenant.due_day
                new_due = self.due_day_spin.value()
                changes.append(f"Due day changed from {old_due} to {new_due}")
            
            # Check rental period changes
            original_rental_period = getattr(self.tenant, 'rental_period', {})
            new_start_date = self.lease_start_date.date().toString('yyyy-MM-dd')
            new_end_date = self.lease_end_date.date().toString('yyyy-MM-dd')
            
            # Handle both old format (list/tuple) and new format (dict)
            if isinstance(original_rental_period, dict):
                old_start = original_rental_period.get('start_date', '')
                old_end = original_rental_period.get('end_date', '')
            elif isinstance(original_rental_period, (list, tuple)) and len(original_rental_period) >= 2:
                old_start = original_rental_period[0] if original_rental_period[0] else ''
                old_end = original_rental_period[1] if original_rental_period[1] else ''
            else:
                old_start = ''
                old_end = ''
            
            if old_start != new_start_date or old_end != new_end_date:
                changes.append(f"Rental period changed from {old_start} to {old_end} → {new_start_date} to {new_end_date}")
            
            # Update basic information
            old_status = self.tenant.account_status
            self.tenant.name = self.name_edit.text().strip()
            self.tenant.notes = self.notes_edit.toPlainText().strip()
            self.tenant.account_status = self.status_combo.currentText().lower()
            
            # Track status change for override handling
            new_status = self.status_combo.currentText().lower()
            if old_status != new_status:
                changes.append(f"Account status changed from '{old_status}' to '{new_status}'")
            
            # Update financial information
            self.tenant.rent_amount = self.rent_amount_spin.value()
            self.tenant.deposit_amount = self.deposit_amount_spin.value()
            self.tenant.due_day = self.due_day_spin.value()
            self.tenant.delinquency_balance = self.delinquency_balance_spin.value()
            self.tenant.overpayment_credit = self.overpayment_credit_spin.value()
            
            # Update contact information
            contact_info = {
                'phone': self.phone_edit.text().strip(),
                'email': self.email_edit.text().strip(),
                'contact': self.legacy_contact_edit.text().strip(),
                'emergency_contact': self.emergency_contact_edit.toPlainText().strip()
            }
            self.tenant.contact_info = contact_info
            
            # Update notification preferences
            notification_methods = []
            if self.notify_system_check.isChecked():
                notification_methods.append('system')
            if self.notify_email_check.isChecked():
                notification_methods.append('email')
            if self.notify_sms_check.isChecked():
                notification_methods.append('sms')
            
            notification_types = []
            if self.notify_rent_due_check.isChecked():
                notification_types.append('rent_due')
            if self.notify_payment_overdue_check.isChecked():
                notification_types.append('payment_overdue')
            if self.notify_lease_expiry_check.isChecked():
                notification_types.append('lease_expiry')
            if self.notify_maintenance_check.isChecked():
                notification_types.append('maintenance')
            if self.notify_general_check.isChecked():
                notification_types.append('general')
            
            notification_preferences = {
                'methods': notification_methods,
                'types': notification_types,
                'timing': {
                    'rent_reminder_days': self.rent_reminder_days_spin.value(),
                    'overdue_notice_days': self.overdue_notice_days_spin.value(),
                    'lease_expiry_days': self.lease_expiry_days_spin.value()
                },
                'templates': {
                    'rent_due': self.rent_due_template_edit.toPlainText().strip(),
                    'overdue': self.overdue_template_edit.toPlainText().strip()
                }
            }
            
            # Add notification preferences to tenant
            self.tenant.notification_preferences = notification_preferences
            
            # Update lease information
            start_date = self.lease_start_date.date().toString('yyyy-MM-dd')
            end_date = self.lease_end_date.date().toString('yyyy-MM-dd')
            
            self.tenant.rental_period = {
                'start_date': start_date,
                'end_date': end_date,
                'lease_type': self.lease_type_combo.currentText()
            }
            
            # Add automatic notes if changes were made
            if changes:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                change_note = f"[{timestamp}] Tenant details updated: " + "; ".join(changes)
                self.tenant.add_note(change_note)
            
            # Save tenant data
            self.rent_tracker.tenant_manager.update_tenant(self.tenant)
            
            # If status changed to inactive/terminated, set $0 overrides for remaining months
            if new_status in ['Inactive', 'Terminated'] and old_status != new_status:
                from datetime import date
                today = date.today()
                
                # Check if overrides already exist for current month
                current_month_key = f"{today.year}-{today.month:02d}"
                if not hasattr(self.tenant, 'monthly_exceptions'):
                    self.tenant.monthly_exceptions = {}
                
                # Only add overrides if they don't already exist
                if current_month_key not in self.tenant.monthly_exceptions:
                    # Set overrides for current and next 5 years worth of months
                    end_date = date(today.year + 5, 12, 31)
                    self.rent_tracker.set_range_override(
                        self.tenant.name,
                        today,
                        end_date,
                        0.0,
                        notes=f"Account {new_status.lower()}: rent set to $0"
                    )
            
            # If status changed to active and it had $0 overrides, remove them
            if new_status == 'Active' and old_status != new_status:
                # Clear any existing overrides when reactivating
                if hasattr(self.tenant, 'monthly_exceptions'):
                    # Clear all existing overrides
                    self.tenant.monthly_exceptions.clear()
                    self.rent_tracker.tenant_manager.update_tenant(self.tenant)
            
            # Trigger recalculation for delinquency and status
            # This is needed when rental periods change
            if hasattr(self.rent_tracker, 'check_and_update_delinquency'):
                # Pass the specific tenant ID for targeted recalculation
                self.rent_tracker.check_and_update_delinquency(target_tenant_id=self.tenant.tenant_id)
            
            QMessageBox.information(self, "Success", "Tenant details updated successfully!")
            self.tenant_updated.emit()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save tenant details: {str(e)}")
            logger.error("TenantDetailsDialog", f"Failed to save tenant details: {e}")
