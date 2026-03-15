from typing import Optional, Any
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, 
                             QPushButton, QMessageBox, QTextEdit, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime

from assets.Logger import Logger
logger = Logger()
class CreditConversionDialog(QDialog):
    """Dialog for converting between overpayment credit and service credit"""
    credit_converted = pyqtSignal()
    
    def __init__(self, parent=None, tenant=None, rent_tracker=None):
        super().__init__(parent)
        logger.debug("CreditConversionDialog", f"Initializing CreditConversionDialog for tenant {tenant.name if tenant else 'Unknown'}")
        self.tenant = tenant
        self.rent_tracker = rent_tracker
        
        # Validate required dependencies
        if not self.tenant:
            logger.error("CreditConversionDialog", "No tenant provided for credit conversion")
            QMessageBox.critical(parent, 'Error', 'No tenant provided for credit conversion.')
            self.reject()
            return
            
        if not self.rent_tracker:
            logger.warning("CreditConversionDialog", "No rent tracker available - changes may not be saved")
            QMessageBox.warning(parent, 'Warning', 'No rent tracker available. Changes may not be saved.')
        
        self.setWindowTitle(f'Credit Conversion - {tenant.name if tenant else "Unknown Tenant"}')
        self.setFixedSize(550, 400)
        self.init_ui()
        logger.info("CreditConversionDialog", f"CreditConversionDialog initialized for {tenant.name if tenant else 'Unknown'}")
    
    def init_ui(self):
        logger.debug("CreditConversionDialog", "Initializing UI")
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f'Credit Conversion for {self.tenant.name if self.tenant else "Unknown Tenant"}')
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0056b3; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current balances display
        balances_group = QGroupBox("Current Credit Balances")
        balances_layout = QVBoxLayout()
        
        overpayment_credit = getattr(self.tenant, 'overpayment_credit', 0.0) if self.tenant else 0.0
        service_credit = getattr(self.tenant, 'service_credit', 0.0) if self.tenant else 0.0
        
        overpayment_label = QLabel(f'Overpayment Credit: ${overpayment_credit:.2f}')
        overpayment_label.setStyleSheet("""
            font-size: 14px;
            color: #0066cc;
            background-color: #e6f3ff;
            padding: 8px;
            border: 1px solid #b3d9ff;
            border-radius: 4px;
        """)
        
        service_label = QLabel(f'Service Credit: ${service_credit:.2f}')
        service_label.setStyleSheet("""
            font-size: 14px;
            color: #28a745;
            background-color: #d4edda;
            padding: 8px;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
        """)
        
        balances_layout.addWidget(overpayment_label)
        balances_layout.addWidget(service_label)
        balances_group.setLayout(balances_layout)
        layout.addWidget(balances_group)
        
        # Conversion options
        conversion_group = QGroupBox("Convert Credits")
        conversion_layout = QVBoxLayout()
        
        # Convert overpayment to service credit
        overpay_to_service_layout = QHBoxLayout()
        overpay_to_service_label = QLabel('Convert Overpayment → Service Credit:')
        overpay_to_service_label.setStyleSheet("font-weight: bold; min-width: 220px;")
        
        self.overpay_to_service_input = QDoubleSpinBox()
        self.overpay_to_service_input.setMinimum(0.00)
        self.overpay_to_service_input.setMaximum(overpayment_credit)
        self.overpay_to_service_input.setDecimals(2)
        self.overpay_to_service_input.setPrefix('$')
        self.overpay_to_service_input.setValue(overpayment_credit)
        self.overpay_to_service_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        overpay_to_service_btn = QPushButton('Convert →')
        overpay_to_service_btn.clicked.connect(self.convert_overpayment_to_service)
        overpay_to_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 15px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        
        overpay_to_service_layout.addWidget(overpay_to_service_label)
        overpay_to_service_layout.addWidget(self.overpay_to_service_input)
        overpay_to_service_layout.addWidget(overpay_to_service_btn)
        
        # Convert service credit to overpayment
        service_to_overpay_layout = QHBoxLayout()
        service_to_overpay_label = QLabel('Convert Service Credit → Overpayment:')
        service_to_overpay_label.setStyleSheet("font-weight: bold; min-width: 220px;")
        
        self.service_to_overpay_input = QDoubleSpinBox()
        self.service_to_overpay_input.setMinimum(0.00)
        self.service_to_overpay_input.setMaximum(service_credit)
        self.service_to_overpay_input.setDecimals(2)
        self.service_to_overpay_input.setPrefix('$')
        self.service_to_overpay_input.setValue(0.00)
        self.service_to_overpay_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        service_to_overpay_btn = QPushButton('Convert →')
        service_to_overpay_btn.clicked.connect(self.convert_service_to_overpayment)
        service_to_overpay_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 15px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        service_to_overpay_layout.addWidget(service_to_overpay_label)
        service_to_overpay_layout.addWidget(self.service_to_overpay_input)
        service_to_overpay_layout.addWidget(service_to_overpay_btn)
        
        conversion_layout.addLayout(overpay_to_service_layout)
        conversion_layout.addLayout(service_to_overpay_layout)
        
        # Notes section
        notes_label = QLabel('Conversion Notes (Optional):')
        notes_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        conversion_layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter reason for credit conversion...")
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setStyleSheet("""
            padding: 8px;
            font-size: 12px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        """)
        conversion_layout.addWidget(self.notes_input)
        
        conversion_group.setLayout(conversion_layout)
        layout.addWidget(conversion_group)
        
        # Info note
        info_label = QLabel("""
        💡 Credit Conversion Information:
        • Overpayment Credit: Created when payments exceed rent amount
        • Service Credit: Earned through services performed for landlord
        • Both can be applied as rent payments but are tracked separately
        """)
        info_label.setStyleSheet("""
            color: #6c757d;
            font-size: 11px;
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
        
        # Close button
        buttons_layout = QHBoxLayout()
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
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
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def convert_overpayment_to_service(self):
        """Convert overpayment credit to service credit"""
        logger.debug("CreditConversionDialog", f"Attempting to convert overpayment to service credit for {self.tenant.name if self.tenant else 'Unknown'}")
        if not self.tenant:
            logger.error("CreditConversionDialog", "No tenant available for conversion")
            QMessageBox.critical(self, 'Error', 'No tenant available for conversion.')
            return
            
        amount = self.overpay_to_service_input.value()
        if amount <= 0:
            logger.warning("CreditConversionDialog", f"Invalid conversion amount: ${amount}")
            QMessageBox.warning(self, 'Invalid Amount', 'Please enter a valid conversion amount.')
            return
        
        available_overpayment = getattr(self.tenant, 'overpayment_credit', 0.0)
        if amount > available_overpayment:
            QMessageBox.warning(self, 'Insufficient Credit', 
                f'Cannot convert ${amount:.2f} when only ${available_overpayment:.2f} overpayment credit is available.')
            return
        
        try:
            # Reduce overpayment credit
            self.tenant.overpayment_credit -= amount
            
            # Increase service credit
            if not hasattr(self.tenant, 'service_credit'):
                self.tenant.service_credit = 0.0
            self.tenant.service_credit += amount
            
            # Add to service credit history
            if not hasattr(self.tenant, 'service_credit_history'):
                self.tenant.service_credit_history = []
            
            notes = self.notes_input.toPlainText().strip()
            conversion_record = {
                'amount': amount,
                'service_type': 'Credit Conversion',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'notes': f'Converted from overpayment credit. {notes}' if notes else 'Converted from overpayment credit.',
                'transaction_type': 'converted',
                'timestamp': datetime.now().isoformat()
            }
            
            self.tenant.service_credit_history.append(conversion_record)
            
            # Note entry
            try:
                if hasattr(self.tenant, 'add_note'):
                    self.tenant.add_note(f"Converted ${amount:.2f} Overpayment → Service Credit. {notes}")
                else:
                    existing = getattr(self.tenant, 'notes', '') or ''
                    line = f"Converted ${amount:.2f} Overpayment → Service Credit. {notes}".strip()
                    self.tenant.notes = (existing + "\n" + line).strip() if existing else line
            except Exception:
                pass

            # Save changes
            if self.rent_tracker:
                self.rent_tracker.save_tenants()
            else:
                QMessageBox.warning(self, 'Warning', 'Changes could not be saved (no rent tracker available).')
            
            # Show confirmation
            logger.info("CreditConversionDialog", f"Successfully converted ${amount:.2f} from overpayment to service credit for {self.tenant.name}")
            QMessageBox.information(self, 'Conversion Complete',
                f'Successfully converted ${amount:.2f} from overpayment credit to service credit.\n\n'
                f'New Overpayment Credit: ${self.tenant.overpayment_credit:.2f}\n'
                f'New Service Credit: ${self.tenant.service_credit:.2f}')
            
            # Refresh display and close
            self.credit_converted.emit()
            self.close()
            
        except Exception as e:
            logger.error("CreditConversionDialog", f"Failed to convert overpayment credit: {str(e)}")
            QMessageBox.critical(self, 'Error', f'Failed to convert credit: {str(e)}')
    
    def convert_service_to_overpayment(self):
        """Convert service credit to overpayment credit"""
        logger.debug("CreditConversionDialog", f"Attempting to convert service to overpayment credit for {self.tenant.name if self.tenant else 'Unknown'}")
        if not self.tenant:
            logger.error("CreditConversionDialog", "No tenant available for conversion")
            QMessageBox.critical(self, 'Error', 'No tenant available for conversion.')
            return
            
        amount = self.service_to_overpay_input.value()
        if amount <= 0:
            logger.warning("CreditConversionDialog", f"Invalid conversion amount: ${amount}")
            QMessageBox.warning(self, 'Invalid Amount', 'Please enter a valid conversion amount.')
            return
        
        available_service = getattr(self.tenant, 'service_credit', 0.0)
        if amount > available_service:
            QMessageBox.warning(self, 'Insufficient Credit', 
                f'Cannot convert ${amount:.2f} when only ${available_service:.2f} service credit is available.')
            return
        
        try:
            # Reduce service credit
            self.tenant.service_credit -= amount
            
            # Increase overpayment credit
            if not hasattr(self.tenant, 'overpayment_credit'):
                self.tenant.overpayment_credit = 0.0
            self.tenant.overpayment_credit += amount
            
            # Add to service credit history (as negative/used entry)
            if not hasattr(self.tenant, 'service_credit_history'):
                self.tenant.service_credit_history = []
            
            notes = self.notes_input.toPlainText().strip()
            conversion_record = {
                'amount': -amount,  # Negative because it's being used/converted
                'service_type': 'Credit Conversion',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'notes': f'Converted to overpayment credit. {notes}' if notes else 'Converted to overpayment credit.',
                'transaction_type': 'converted',
                'timestamp': datetime.now().isoformat()
            }
            
            self.tenant.service_credit_history.append(conversion_record)
            
            # Note entry
            try:
                if hasattr(self.tenant, 'add_note'):
                    self.tenant.add_note(f"Converted ${amount:.2f} Service Credit → Overpayment. {notes}")
                else:
                    existing = getattr(self.tenant, 'notes', '') or ''
                    line = f"Converted ${amount:.2f} Service Credit → Overpayment. {notes}".strip()
                    self.tenant.notes = (existing + "\n" + line).strip() if existing else line
            except Exception:
                pass

            # Save changes
            if self.rent_tracker:
                self.rent_tracker.save_tenants()
            else:
                QMessageBox.warning(self, 'Warning', 'Changes could not be saved (no rent tracker available).')
            
            # Show confirmation
            logger.info("CreditConversionDialog", f"Successfully converted ${amount:.2f} from service to overpayment credit for {self.tenant.name}")
            QMessageBox.information(self, 'Conversion Complete',
                f'Successfully converted ${amount:.2f} from service credit to overpayment credit.\n\n'
                f'New Service Credit: ${self.tenant.service_credit:.2f}\n'
                f'New Overpayment Credit: ${self.tenant.overpayment_credit:.2f}')
            
            # Refresh display and close
            self.credit_converted.emit()
            self.close()
            
        except Exception as e:
            logger.error("CreditConversionDialog", f"Failed to convert service credit: {str(e)}")
            QMessageBox.critical(self, 'Error', f'Failed to convert credit: {str(e)}')
