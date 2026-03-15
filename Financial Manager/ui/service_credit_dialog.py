from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, 
                             QLineEdit, QPushButton, QMessageBox, QDateEdit, QTextEdit, QComboBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from datetime import datetime, date
from assets.Logger import Logger

logger = Logger()

class ServiceCreditDialog(QDialog):
    """Dialog for adding service credits to a tenant account"""
    credit_added = pyqtSignal()
    
    def __init__(self, parent=None, tenant=None, rent_tracker=None):
        super().__init__(parent)
        logger.debug("ServiceCreditDialog", f"Initializing ServiceCreditDialog for tenant {tenant.name if tenant else 'Unknown'}")
        self.tenant = tenant
        self.rent_tracker = rent_tracker
        
        self.setWindowTitle(f'Add Service Credit - {tenant.name if tenant else "Unknown Tenant"}')
        self.setFixedSize(500, 450)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f'Add Service Credit for {self.tenant.name if self.tenant else "Unknown Tenant"}')
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0056b3; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current service credit balance
        current_credit = getattr(self.tenant, 'service_credit', 0.0) if self.tenant else 0.0
        balance_label = QLabel(f'Current Service Credit Balance: ${current_credit:.2f}')
        balance_label.setStyleSheet("""
            font-size: 14px;
            color: #28a745;
            background-color: #d4edda;
            padding: 10px;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
            margin-bottom: 15px;
        """)
        balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(balance_label)
        
        # Service type section
        service_layout = QHBoxLayout()
        service_label = QLabel('Service Type:')
        service_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.service_combo = QComboBox()
        self.service_combo.addItems([
            'Window Washing', 'Lawn Care', 'Snow Removal', 'Cleaning', 
            'Maintenance Work', 'Property Improvement', 'Other'
        ])
        self.service_combo.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.service_combo.currentTextChanged.connect(self.on_service_type_changed)
        
        service_layout.addWidget(service_label)
        service_layout.addWidget(self.service_combo)
        layout.addLayout(service_layout)
        
        # Other service type input (hidden by default)
        other_layout = QHBoxLayout()
        other_label = QLabel('Specify Service:')
        other_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.other_service_input = QLineEdit()
        self.other_service_input.setPlaceholderText("Enter service type...")
        self.other_service_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.other_service_input.hide()
        
        other_layout.addWidget(other_label)
        other_layout.addWidget(self.other_service_input)
        self.other_layout = other_layout
        layout.addLayout(other_layout)
        
        # Credit amount section
        amount_layout = QHBoxLayout()
        amount_label = QLabel('Credit Amount:')
        amount_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMinimum(0.01)
        self.amount_input.setMaximum(10000.00)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix('$')
        self.amount_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount_input)
        layout.addLayout(amount_layout)
        
        # Date section
        date_layout = QHBoxLayout()
        date_label = QLabel('Service Date:')
        date_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setMinimumWidth(200)
        calendar = self.date_input.calendarWidget()
        if calendar:
            calendar.setMinimumSize(300, 200)
        self.date_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_input)
        layout.addLayout(date_layout)
        
        # Description/Notes section
        notes_label = QLabel('Service Description (Optional):')
        notes_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter details about the service performed...")
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setStyleSheet("""
            padding: 8px;
            font-size: 14px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        """)
        layout.addWidget(self.notes_input)
        
        # Apply credit to rent checkbox info
        info_label = QLabel("""
        💡 This credit will be added to the tenant's service credit balance.
        You can then apply it as a "Service Credit" payment in the payment dialog.
        """)
        info_label.setStyleSheet("""
            color: #6c757d;
            font-size: 12px;
            background-color: #f8f9fa;
            padding: 10px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            margin: 10px 0;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Spacer
        layout.addStretch()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        # Add credit button
        add_btn = QPushButton('Add Service Credit')
        add_btn.clicked.connect(self.add_credit)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
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
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        
        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def on_service_type_changed(self, service_type):
        """Show/hide other service input based on selection"""
        if service_type == 'Other':
            self.other_service_input.show()
        else:
            self.other_service_input.hide()
    
    def add_credit(self):
        """Add the service credit to the tenant's account"""
        if not self.tenant or not self.rent_tracker:
            QMessageBox.critical(self, 'Error', 'Tenant or rent tracker not available.')
            return
        
        # Get form data
        service_type = self.service_combo.currentText()
        if service_type == 'Other':
            service_type = self.other_service_input.text().strip()
            if not service_type:
                QMessageBox.warning(self, 'Missing Information', 'Please specify the service type.')
                return
        
        amount = self.amount_input.value()
        if amount <= 0:
            QMessageBox.warning(self, 'Invalid Amount', 'Please enter a valid credit amount.')
            return
        
        # Convert QDate to Python date
        qdate = self.date_input.date()
        service_date = date(qdate.year(), qdate.month(), qdate.day())
        notes = self.notes_input.toPlainText().strip()
        
        # Add service credit to tenant
        try:
            # Ensure service credit fields exist
            if not hasattr(self.tenant, 'service_credit'):
                self.tenant.service_credit = 0.0
            if not hasattr(self.tenant, 'service_credit_history'):
                self.tenant.service_credit_history = []
            
            # Add to service credit balance
            self.tenant.service_credit += amount
            
            # Create credit record
            credit_record = {
                'amount': amount,
                'service_type': service_type,
                'date': service_date.strftime('%Y-%m-%d'),
                'notes': notes,
                'transaction_type': 'earned',
                'timestamp': datetime.now().isoformat()
            }
            
            self.tenant.service_credit_history.append(credit_record)
            
            # Append note entry about service credit earned
            try:
                if hasattr(self.tenant, 'add_note'):
                    self.tenant.add_note(f"Service Credit Earned: ${amount:.2f} for '{service_type}' on {service_date.strftime('%Y-%m-%d')}. {('Notes: '+notes) if notes else ''}")
                else:
                    # Fallback: append to string notes
                    existing = getattr(self.tenant, 'notes', '') or ''
                    new_line = f"Service Credit Earned: ${amount:.2f} for '{service_type}' on {service_date.strftime('%Y-%m-%d')}. {('Notes: '+notes) if notes else ''}".strip()
                    self.tenant.notes = (existing + "\n" + new_line).strip() if existing else new_line
            except Exception:
                pass

            # Save changes
            self.rent_tracker.save_tenants()
            
            # Show confirmation
            QMessageBox.information(self, 'Service Credit Added',
                f'Service credit of ${amount:.2f} has been added to {self.tenant.name}\'s account.\n\n'
                f'Service: {service_type}\n'
                f'Date: {service_date.strftime("%B %d, %Y")}\n'
                f'New Credit Balance: ${self.tenant.service_credit:.2f}')
            
            # Emit signal and close
            self.credit_added.emit()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to add service credit: {str(e)}')
