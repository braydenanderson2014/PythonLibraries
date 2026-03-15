"""
Legacy Data Import Dialog
Allows importing tenant rent data from legacy JSON format
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QTextEdit, QMessageBox,
                             QLineEdit, QFormLayout, QGroupBox, QScrollArea,
                             QWidget, QDateEdit, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont
import json
from datetime import datetime
from typing import Dict, List, Any
from assets.Logger import Logger

logger = Logger()

class TenantInfoDialog(QDialog):
    """Dialog to collect missing tenant information"""
    
    def __init__(self, parent, tenant_name: str, legacy_data: Dict):
        super().__init__(parent)
        logger.debug("TenantInfoDialog", f"Initializing TenantInfoDialog for tenant {tenant_name}")
        self.tenant_name = tenant_name
        self.legacy_data = legacy_data
        self.tenant_info = {}
        
        self.setWindowTitle(f"Complete Tenant Information: {tenant_name}")
        self.setModal(True)
        self.resize(500, 600)
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"Please provide additional information for tenant: {self.tenant_name}")
        header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QFormLayout()
        
        # Tenant Name (pre-filled, can be edited)
        self.name_edit = QLineEdit(self.tenant_name)
        form_layout.addRow("Tenant Name:", self.name_edit)
        
        # Rent Amount (from legacy data)
        rent_amount = self.legacy_data.get('rent', 0.0)
        try:
            # Ensure rent_amount is a valid number
            rent_value = float(rent_amount) if rent_amount else 0.0
            self.rent_edit = QLineEdit(f"{rent_value:.2f}")
        except (ValueError, TypeError):
            self.rent_edit = QLineEdit("0.00")
        form_layout.addRow("Monthly Rent ($):", self.rent_edit)
        
        # Deposit Amount
        self.deposit_edit = QLineEdit("0.00")
        form_layout.addRow("Deposit Amount ($):", self.deposit_edit)
        
        # Rental Period Start
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        # Try to infer start date from earliest payment
        earliest_date = self._get_earliest_payment_date()
        if earliest_date:
            self.start_date_edit.setDate(QDate(earliest_date.year, earliest_date.month, 1))
        else:
            self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        form_layout.addRow("Lease Start Date:", self.start_date_edit)
        
        # Rental Period End
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addYears(1))
        form_layout.addRow("Lease End Date:", self.end_date_edit)
        
        # Rent Due Date (day of month)
        self.due_date_edit = QLineEdit("1")
        form_layout.addRow("Rent Due Day (1-31):", self.due_date_edit)
        
        # Contact Information Group
        contact_group = QGroupBox("Contact Information")
        contact_layout = QFormLayout()
        
        self.phone_edit = QLineEdit()
        contact_layout.addRow("Phone:", self.phone_edit)
        
        self.email_edit = QLineEdit()
        contact_layout.addRow("Email:", self.email_edit)
        
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(60)
        contact_layout.addRow("Address:", self.address_edit)
        
        contact_group.setLayout(contact_layout)
        form_layout.addRow(contact_group)
        
        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Any additional notes about this tenant...")
        form_layout.addRow("Notes:", self.notes_edit)
        
        # Account Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Active', 'Inactive', 'Notice Given', 'Eviction'])
        form_layout.addRow("Account Status:", self.status_combo)
        
        scroll_widget.setLayout(form_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Summary of legacy data being imported
        summary_group = QGroupBox("Legacy Data Summary")
        summary_layout = QVBoxLayout()
        summary_text = QTextEdit()
        summary_text.setReadOnly(True)
        summary_text.setMaximumHeight(100)
        
        payment_count = len(self.legacy_data.get('payments', []))
        na_months = self.legacy_data.get('na_months', {})
        na_count = sum(len(months) for months in na_months.values())
        
        summary_text.setText(
            f"Payments to import: {payment_count}\n"
            f"N/A months: {na_count}\n"
            f"Monthly rent: ${rent_amount:.2f}"
        )
        summary_layout.addWidget(summary_text)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("Import Tenant")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _get_earliest_payment_date(self):
        """Extract earliest payment date from legacy data"""
        payments = self.legacy_data.get('payments', [])
        if not payments:
            return None
        
        earliest = None
        for payment in payments:
            date_str = payment.get('date', '')
            try:
                # Parse MM/DD/YYYY format
                payment_date = datetime.strptime(date_str, '%m/%d/%Y')
                if earliest is None or payment_date < earliest:
                    earliest = payment_date
            except:
                continue
        
        return earliest
    
    def get_tenant_info(self) -> Dict:
        """Collect and validate tenant information"""
        try:
            # Validate and convert rent amount
            rent_text = self.rent_edit.text().strip()
            if not rent_text:
                raise ValueError("Rent amount cannot be empty")
            rent = float(rent_text)
            
            # Validate and convert deposit amount
            deposit_text = self.deposit_edit.text().strip()
            if not deposit_text:
                raise ValueError("Deposit amount cannot be empty")
            deposit = float(deposit_text)
            
            # Validate due day
            due_day_text = self.due_date_edit.text().strip()
            if not due_day_text:
                raise ValueError("Due day cannot be empty")
            due_day = int(due_day_text)
            
            if not (1 <= due_day <= 31):
                raise ValueError("Due day must be between 1 and 31")
            
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            
            if end_date <= start_date:
                raise ValueError("End date must be after start date")
            
            contact_info = {
                'phone': self.phone_edit.text().strip(),
                'email': self.email_edit.text().strip(),
                'address': self.address_edit.toPlainText().strip()
            }
            
            return {
                'name': self.name_edit.text().strip(),
                'rent_amount': rent,
                'deposit_amount': deposit,
                'rental_period': (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
                'rent_due_date': str(due_day),
                'contact_info': contact_info,
                'notes': self.notes_edit.toPlainText().strip(),
                'account_status': self.status_combo.currentText()
            }
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", f"Invalid input: {str(e)}")
            return None
    
    def accept(self):
        info = self.get_tenant_info()
        if info:
            self.tenant_info = info
            super().accept()


class LegacyDataImportDialog(QDialog):
    """Main dialog for importing legacy tenant data"""
    
    data_imported = pyqtSignal()  # Signal emitted when data is successfully imported
    
    def __init__(self, parent, rent_tracker, current_user_id=None):
        super().__init__(parent)
        self.rent_tracker = rent_tracker
        self.current_user_id = current_user_id
        self.legacy_data = None
        self.file_path = None
        
        self.setWindowTitle("Import Legacy Tenant Data")
        self.setModal(True)
        self.resize(700, 500)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Import Legacy Tenant Payment Data")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Description
        desc = QLabel(
            "This tool imports tenant rent payment data from legacy JSON format.\n"
            "For existing tenants, it will add payment history.\n"
            "For new tenants, you'll be prompted to provide additional information."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Legacy Data File:"))
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText("Select a JSON file...")
        file_layout.addWidget(self.file_path_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_button)
        
        layout.addLayout(file_layout)
        
        # Preview area
        preview_label = QLabel("File Preview:")
        preview_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Select a file to preview its contents...")
        layout.addWidget(self.preview_text)
        
        # Options
        options_group = QGroupBox("Import Options")
        options_layout = QVBoxLayout()
        
        self.skip_existing_checkbox = QCheckBox("Skip payments that already exist")
        self.skip_existing_checkbox.setChecked(True)
        options_layout.addWidget(self.skip_existing_checkbox)
        
        self.dry_run_checkbox = QCheckBox("Dry run (preview only, don't save changes)")
        options_layout.addWidget(self.dry_run_checkbox)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.import_button = QPushButton("Import Data")
        self.import_button.clicked.connect(self.import_data)
        self.import_button.setEnabled(False)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def browse_file(self):
        """Open file browser to select legacy data JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Legacy Data File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.file_path_edit.setText(file_path)
            self.load_and_preview_file()
    
    def load_and_preview_file(self):
        """Load and display preview of legacy data file"""
        try:
            with open(self.file_path, 'r') as f:
                self.legacy_data = json.load(f)
            
            # Generate preview
            preview_lines = ["Legacy Data Preview:\n"]
            preview_lines.append(f"Total tenants: {len(self.legacy_data)}\n\n")
            
            for tenant_name, data in self.legacy_data.items():
                payment_count = len(data.get('payments', []))
                rent = data.get('rent', 0.0)
                na_months = data.get('na_months', {})
                na_count = sum(len(months) for months in na_months.values())
                
                preview_lines.append(f"• {tenant_name}:")
                preview_lines.append(f"  - Monthly Rent: ${rent:.2f}")
                preview_lines.append(f"  - Payments: {payment_count}")
                preview_lines.append(f"  - N/A Months: {na_count}\n")
            
            self.preview_text.setText('\n'.join(preview_lines))
            self.import_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
            self.preview_text.clear()
            self.import_button.setEnabled(False)
            self.legacy_data = None
    
    def import_data(self):
        """Process and import the legacy data"""
        if not self.legacy_data:
            QMessageBox.warning(self, "No Data", "Please select a file first.")
            return
        
        dry_run = self.dry_run_checkbox.isChecked()
        skip_existing = self.skip_existing_checkbox.isChecked()
        
        results = {
            'tenants_created': 0,
            'tenants_updated': 0,
            'payments_added': 0,
            'payments_skipped': 0,
            'errors': []
        }
        
        try:
            for tenant_name, tenant_data in self.legacy_data.items():
                try:
                    result = self._import_tenant_data(
                        tenant_name, 
                        tenant_data, 
                        skip_existing=skip_existing,
                        dry_run=dry_run
                    )
                    
                    if result['created']:
                        results['tenants_created'] += 1
                    else:
                        results['tenants_updated'] += 1
                    
                    results['payments_added'] += result['payments_added']
                    results['payments_skipped'] += result['payments_skipped']
                    
                except Exception as e:
                    error_msg = f"Error importing {tenant_name}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error("LegacyDataImportDialog", error_msg)
            
            # Show results
            self._show_import_results(results, dry_run)
            
            if not dry_run and (results['tenants_created'] > 0 or results['tenants_updated'] > 0):
                # Force save all changes
                self.rent_tracker.tenant_manager.save()
                # Emit signal to refresh UI
                self.data_imported.emit()
                
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import data: {str(e)}")
    
    def _import_tenant_data(self, tenant_name: str, tenant_data: Dict, 
                           skip_existing: bool = True, dry_run: bool = False) -> Dict:
        """Import data for a single tenant"""
        result = {
            'created': False,
            'payments_added': 0,
            'payments_skipped': 0
        }
        
        # Check if tenant exists
        tenant = self._find_tenant_by_name(tenant_name)
        
        if not tenant:
            # New tenant - collect additional info
            if dry_run:
                logger.info("LegacyDataImportDialog", f"[DRY RUN] Would create new tenant: {tenant_name}")
                result['created'] = True
                result['payments_added'] = len(tenant_data.get('payments', []))
                return result
            
            # Show dialog to collect missing info
            info_dialog = TenantInfoDialog(self, tenant_name, tenant_data)
            if info_dialog.exec() != QDialog.DialogCode.Accepted:
                raise Exception("Tenant creation cancelled by user")
            
            tenant_info = info_dialog.tenant_info
            
            # Convert rental_period to new dict format if it's a tuple
            rental_period = tenant_info['rental_period']
            if isinstance(rental_period, (list, tuple)) and len(rental_period) == 2:
                # Old format: (start_date, end_date) -> convert to new dict format
                rental_period = {
                    'start_date': rental_period[0],
                    'end_date': rental_period[1],
                    'lease_type': 'Fixed Term'
                }
            
            # Create new tenant
            tenant = self.rent_tracker.tenant_manager.add_tenant(
                name=tenant_info['name'],
                rental_period=rental_period,
                rent_amount=tenant_info['rent_amount'],
                deposit_amount=tenant_info['deposit_amount'],
                contact_info=tenant_info['contact_info'],
                notes=tenant_info['notes'],
                rent_due_date=tenant_info['rent_due_date'],
                user_id=self.current_user_id
            )
            
            # Initialize payment_history if not present
            if not hasattr(tenant, 'payment_history'):
                tenant.payment_history = []
            
            # Set account status
            tenant.account_status = tenant_info['account_status']
            result['created'] = True
        
        # Import payments
        payments = tenant_data.get('payments', [])
        for payment in payments:
            try:
                # Parse payment data
                date_str = payment.get('date', '')
                amount = float(payment.get('amount', 0))
                month_name = payment.get('month', '')
                method = payment.get('method', 'Unknown')
                
                # Parse date (MM/DD/YYYY format)
                payment_date = datetime.strptime(date_str, '%m/%d/%Y')
                payment_year = payment_date.year
                payment_date_month = payment_date.month
                
                # Determine which month/year this payment is for
                # Use the month_name if provided, otherwise use payment date month
                if month_name:
                    month_num = self._month_name_to_number(month_name)
                    if month_num:
                        # Use the month from the payment data
                        year = payment_year
                        month = month_num
                        
                        # If payment month is AFTER payment date month, it's likely for a previous month
                        # (e.g., paid in July for August means they paid early, use payment year)
                        # If payment month is BEFORE payment date month, it's for same year
                        # (e.g., paid in July for June means they paid late, use payment year)
                        # Exception: if payment is for a month much earlier and we haven't seen it
                        # yet based on rental period, it should be the same year
                        # For now, always use payment year unless month is much later (>6 months)
                        if month > payment_date_month:
                            months_diff = month - payment_date_month
                            if months_diff > 6:
                                # Likely for next year
                                year = payment_year + 1
                    else:
                        # Failed to parse month name, fall back to payment date
                        year = payment_year
                        month = payment_date_month
                else:
                    # No month name provided, use payment date
                    year = payment_year
                    month = payment_date_month
                
                if dry_run:
                    result['payments_added'] += 1
                    continue
                
                # Check if payment already exists
                if skip_existing and self._payment_exists(tenant, year, month, payment_date.day, amount):
                    result['payments_skipped'] += 1
                    continue
                
                # Add payment using tenant name (not tenant_id)
                self.rent_tracker.add_payment(
                    tenant.name,  # Use tenant name instead of tenant_id
                    amount,
                    payment_type=method,
                    payment_date=payment_date,
                    payment_month=f"{year}-{month:02d}"
                )
                result['payments_added'] += 1
                
            except Exception as e:
                logger.warning("LegacyDataImportDialog", f"Failed to import payment: {payment}, error: {e}")
                continue
        
        # Import N/A months
        na_months = tenant_data.get('na_months', {})
        for year_str, months in na_months.items():
            try:
                year = int(year_str)
                for month_name in months:
                    # Convert month name to number
                    month_num = self._month_name_to_number(month_name)
                    if month_num and not dry_run:
                        # Set monthly override for N/A status
                        month_key = f"{year}-{month_num:02d}"
                        if not hasattr(tenant, 'monthly_status'):
                            tenant.monthly_status = {}
                        tenant.monthly_status[month_key] = 'N/A'
            except Exception as e:
                logger.warning("LegacyDataImportDialog", f"Failed to import N/A month: {e}")
        
        # Save changes
        if not dry_run:
            self.rent_tracker.tenant_manager.save()
            # Recalculate delinquency
            self.rent_tracker.check_and_update_delinquency(tenant.tenant_id)
        
        return result
    
    def _find_tenant_by_name(self, name: str):
        """Find tenant by name (case-insensitive)"""
        name_lower = name.lower().strip()
        for tenant in self.rent_tracker.tenant_manager.list_tenants():
            if tenant.name.lower().strip() == name_lower:
                return tenant
        return None
    
    def _payment_exists(self, tenant, year: int, month: int, day: int, amount: float) -> bool:
        """Check if a payment already exists"""
        if not hasattr(tenant, 'payment_history'):
            return False
        
        for payment in tenant.payment_history:
            if (payment.get('year') == year and 
                payment.get('month') == month and
                payment.get('day') == day and
                abs(payment.get('amount', 0) - amount) < 0.01):
                return True
        return False
    
    def _month_name_to_number(self, month_name: str) -> int:
        """Convert month name to number"""
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        return months.get(month_name.lower(), None)
    
    def _show_import_results(self, results: Dict, dry_run: bool):
        """Display import results to user"""
        title = "Import Results (Dry Run)" if dry_run else "Import Results"
        
        message_lines = []
        
        if dry_run:
            message_lines.append("DRY RUN - No changes were saved\n")
        
        message_lines.append(f"Tenants created: {results['tenants_created']}")
        message_lines.append(f"Tenants updated: {results['tenants_updated']}")
        message_lines.append(f"Payments added: {results['payments_added']}")
        message_lines.append(f"Payments skipped: {results['payments_skipped']}")
        
        if results['errors']:
            message_lines.append(f"\nErrors: {len(results['errors'])}")
            for error in results['errors'][:5]:  # Show first 5 errors
                message_lines.append(f"  • {error}")
            if len(results['errors']) > 5:
                message_lines.append(f"  ... and {len(results['errors']) - 5} more")
        
        message = '\n'.join(message_lines)
        
        if results['errors']:
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)
        
        if not dry_run:
            self.accept()
