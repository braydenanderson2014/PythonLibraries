from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QDateEdit, QTextEdit, QDoubleSpinBox
from PyQt6.QtCore import Qt
from datetime import date

from assets.Logger import Logger
logger = Logger()

class CreateTenantDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("CreateTenantDialog", "Initializing CreateTenantDialog")
        self.setWindowTitle('Create New Tenant')
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        # Name
        layout.addWidget(QLabel('Tenant Name:'))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        # Rental Period
        layout.addWidget(QLabel('Rental Period Start:'))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(date.today())
        self.start_date.setMinimumWidth(200)
        calendar = self.start_date.calendarWidget()
        if calendar:
            calendar.setMinimumSize(300, 200)
        layout.addWidget(self.start_date)
        layout.addWidget(QLabel('Rental Period End:'))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(date.today())
        self.end_date.setMinimumWidth(200)
        calendar = self.end_date.calendarWidget()
        if calendar:
            calendar.setMinimumSize(300, 200)
        layout.addWidget(self.end_date)
        # Rent Amount
        layout.addWidget(QLabel('Monthly Rent Amount:'))
        self.rent_amount = QDoubleSpinBox()
        self.rent_amount.setMaximum(100000)
        self.rent_amount.setPrefix('$')
        layout.addWidget(self.rent_amount)
        # Deposit
        layout.addWidget(QLabel('Deposit Amount:'))
        self.deposit_amount = QDoubleSpinBox()
        self.deposit_amount.setMaximum(100000)
        self.deposit_amount.setPrefix('$')
        layout.addWidget(self.deposit_amount)
        # Rent Due Date
        layout.addWidget(QLabel('Rent Due Date (Day of Month):'))
        self.due_day = QLineEdit()
        self.due_day.setPlaceholderText('e.g. 1 for 1st of month')
        layout.addWidget(self.due_day)
        # Contact Info
        layout.addWidget(QLabel('Contact Information:'))
        
        # Phone Number
        layout.addWidget(QLabel('Phone Number:'))
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText('e.g. (555) 123-4567')
        layout.addWidget(self.phone_edit)
        
        # Email Address
        layout.addWidget(QLabel('Email Address:'))
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText('e.g. tenant@example.com')
        layout.addWidget(self.email_edit)
        
        # Additional Contact Info (legacy field)
        layout.addWidget(QLabel('Additional Contact Info:'))
        self.contact_edit = QLineEdit()
        self.contact_edit.setPlaceholderText('Any additional contact details')
        layout.addWidget(self.contact_edit)
        # Notes
        layout.addWidget(QLabel('Notes:'))
        self.notes_edit = QTextEdit()
        layout.addWidget(self.notes_edit)
        # Buttons
        btn_layout = QHBoxLayout()
        self.submit_btn = QPushButton('Create')
        self.submit_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.submit_btn)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        logger.info("CreateTenantDialog", "CreateTenantDialog initialized")

    def get_data(self):
        logger.debug("CreateTenantDialog", "Getting form data")
        # Build contact info dictionary with phone and email
        contact_info = {}
        
        if self.phone_edit.text().strip():
            contact_info['phone'] = self.phone_edit.text().strip()
        
        if self.email_edit.text().strip():
            contact_info['email'] = self.email_edit.text().strip()
        
        # Keep legacy contact field for backward compatibility
        if self.contact_edit.text().strip():
            contact_info['contact'] = self.contact_edit.text().strip()
        
        return {
            'name': self.name_edit.text().strip(),
            'rental_period': (self.start_date.date().toString('yyyy-MM-dd'), self.end_date.date().toString('yyyy-MM-dd')),
            'rent_amount': self.rent_amount.value(),
            'deposit_amount': self.deposit_amount.value(),
            'rent_due_date': self.due_day.text().strip(),
            'contact_info': contact_info,
            'notes': self.notes_edit.toPlainText().strip()
        }
