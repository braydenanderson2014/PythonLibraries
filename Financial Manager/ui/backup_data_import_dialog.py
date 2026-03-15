"""
Backup Data Import Dialog
Allows importing tenant rent data from backup JSON files
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QTextEdit, QMessageBox,
                             QCheckBox, QGroupBox, QRadioButton, QButtonGroup, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
from datetime import datetime
from typing import Dict, List, Any
from assets.Logger import Logger

logger = Logger()


class BackupDataImportDialog(QDialog):
    """Main dialog for importing tenant backup data"""
    
    data_imported = pyqtSignal()  # Signal emitted when data is successfully imported
    
    def __init__(self, parent, rent_tracker, current_user_id=None):
        super().__init__(parent)
        self.rent_tracker = rent_tracker
        self.current_user_id = current_user_id
        self.backup_data = None
        self.file_path = None
        
        self.setWindowTitle("Import Tenant Backup Data")
        self.setModal(True)
        self.resize(700, 600)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Import Tenant Backup Data")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Description
        desc = QLabel(
            "This tool imports tenant data from backup JSON files.\n"
            "You can restore a tenant's complete data including payment history."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Backup File:"))
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText("Select a backup JSON file...")
        file_layout.addWidget(self.file_path_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_button)
        
        layout.addLayout(file_layout)
        
        # Preview area
        preview_group = QGroupBox("Backup Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setPlaceholderText("Load a backup file to see preview...")
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Import options
        options_group = QGroupBox("Import Options")
        options_layout = QVBoxLayout()
        
        # Import mode selection
        mode_label = QLabel("If tenant already exists:")
        mode_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        options_layout.addWidget(mode_label)
        
        self.mode_group = QButtonGroup(self)
        
        self.merge_radio = QRadioButton("Merge with existing tenant (add payment history)")
        self.merge_radio.setChecked(True)
        self.mode_group.addButton(self.merge_radio, 0)
        options_layout.addWidget(self.merge_radio)
        
        self.replace_radio = QRadioButton("Replace existing tenant completely")
        self.mode_group.addButton(self.replace_radio, 1)
        options_layout.addWidget(self.replace_radio)
        
        self.skip_radio = QRadioButton("Skip if tenant exists")
        self.mode_group.addButton(self.skip_radio, 2)
        options_layout.addWidget(self.skip_radio)
        
        # Additional options
        self.recalc_checkbox = QCheckBox("Recalculate delinquency after import")
        self.recalc_checkbox.setChecked(True)
        options_layout.addWidget(self.recalc_checkbox)
        
        self.dry_run_checkbox = QCheckBox("Dry run (preview changes without importing)")
        options_layout.addWidget(self.dry_run_checkbox)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Results area
        results_group = QGroupBox("Import Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        self.results_text.setPlaceholderText("Import results will appear here...")
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self.import_data)
        self.import_button.setEnabled(False)
        button_layout.addWidget(self.import_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_file(self):
        """Open file dialog to select backup file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.file_path_edit.setText(file_path)
            self.load_backup_file()
    
    def load_backup_file(self):
        """Load and preview the backup file"""
        try:
            with open(self.file_path, 'r') as f:
                self.backup_data = json.load(f)
            
            # Validate backup data structure
            if not self.validate_backup_data():
                return
            
            # Show preview
            self.show_preview()
            self.import_button.setEnabled(True)
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid File", 
                f"Failed to parse JSON file:\n{str(e)}")
            self.backup_data = None
            self.import_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"Failed to load backup file:\n{str(e)}")
            self.backup_data = None
            self.import_button.setEnabled(False)
    
    def validate_backup_data(self) -> bool:
        """Validate the structure of backup data"""
        if not self.backup_data:
            QMessageBox.warning(self, "Invalid Backup", "Backup file is empty.")
            return False
        
        # Check for both single tenant and multi-tenant backup formats
        if 'tenant_data' in self.backup_data:
            # Single tenant backup
            tenant_data = self.backup_data['tenant_data']
            if 'name' not in tenant_data:
                QMessageBox.warning(self, "Invalid Backup", 
                    "Backup file missing required 'name' field.")
                return False
        elif 'tenants' in self.backup_data:
            # Multi-tenant backup
            if not isinstance(self.backup_data['tenants'], list):
                QMessageBox.warning(self, "Invalid Backup", 
                    "Backup file 'tenants' field must be a list.")
                return False
        else:
            QMessageBox.warning(self, "Invalid Backup", 
                "Backup file missing 'tenant_data' or 'tenants' field.")
            return False
        
        return True
    
    def show_preview(self):
        """Display a preview of the backup data"""
        preview_lines = []
        
        if 'tenant_data' in self.backup_data:
            # Single tenant backup
            tenant_data = self.backup_data['tenant_data']
            backup_date = self.backup_data.get('backup_date', 'Unknown')
            
            preview_lines.append(f"Backup Type: Single Tenant")
            preview_lines.append(f"Backup Date: {backup_date}")
            preview_lines.append(f"\nTenant: {tenant_data.get('name', 'Unknown')}")
            preview_lines.append(f"Rent Amount: ${tenant_data.get('rent_amount', 0):.2f}")
            preview_lines.append(f"Delinquency Balance: ${tenant_data.get('delinquency_balance', 0):.2f}")
            preview_lines.append(f"Overpayment Credit: ${tenant_data.get('overpayment_credit', 0):.2f}")
            preview_lines.append(f"Service Credit: ${tenant_data.get('service_credit', 0):.2f}")
            
            payment_count = len(tenant_data.get('payment_history', []))
            preview_lines.append(f"Payment History: {payment_count} payment(s)")
            
        elif 'tenants' in self.backup_data:
            # Multi-tenant backup
            tenants = self.backup_data['tenants']
            backup_date = self.backup_data.get('backup_date', 'Unknown')
            backup_type = self.backup_data.get('backup_type', 'Unknown')
            
            preview_lines.append(f"Backup Type: {backup_type}")
            preview_lines.append(f"Backup Date: {backup_date}")
            preview_lines.append(f"Number of Tenants: {len(tenants)}\n")
            
            for idx, tenant_info in enumerate(tenants[:5], 1):  # Show first 5
                tenant_data = tenant_info.get('tenant_data', {})
                preview_lines.append(f"{idx}. {tenant_data.get('name', 'Unknown')}")
                preview_lines.append(f"   Rent: ${tenant_data.get('rent_amount', 0):.2f}")
                payment_count = len(tenant_data.get('payment_history', []))
                preview_lines.append(f"   Payments: {payment_count}")
            
            if len(tenants) > 5:
                preview_lines.append(f"\n... and {len(tenants) - 5} more tenant(s)")
        
        self.preview_text.setPlainText('\n'.join(preview_lines))
    
    def import_data(self):
        """Process and import the backup data"""
        if not self.backup_data:
            QMessageBox.warning(self, "No Data", "No backup data loaded.")
            return
        
        dry_run = self.dry_run_checkbox.isChecked()
        import_mode = self.mode_group.checkedId()  # 0=merge, 1=replace, 2=skip
        
        results = []
        tenants_to_process = []
        
        # Prepare list of tenants to import
        if 'tenant_data' in self.backup_data:
            # Single tenant backup
            tenants_to_process = [{
                'tenant_data': self.backup_data['tenant_data'],
                'source': self.backup_data.get('tenant_name', 'Unknown')
            }]
        elif 'tenants' in self.backup_data:
            # Multi-tenant backup
            tenants_to_process = self.backup_data['tenants']
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for tenant_info in tenants_to_process:
            tenant_data = tenant_info.get('tenant_data', {})
            tenant_name = tenant_data.get('name')
            
            if not tenant_name:
                results.append(f"❌ Skipped tenant with no name")
                skipped_count += 1
                continue
            
            try:
                # Check if tenant exists
                existing_tenant = self.rent_tracker.get_tenant_by_name(tenant_name)
                
                if existing_tenant:
                    if import_mode == 2:  # Skip
                        results.append(f"⏭️  Skipped existing tenant: {tenant_name}")
                        skipped_count += 1
                        continue
                    elif import_mode == 1:  # Replace
                        if dry_run:
                            results.append(f"[DRY RUN] Would replace tenant: {tenant_name}")
                        else:
                            # Delete and recreate
                            self.rent_tracker.delete_tenant(tenant_name)
                            self._create_tenant_from_backup(tenant_data, results, tenant_name)
                        imported_count += 1
                    else:  # Merge (mode 0)
                        if dry_run:
                            results.append(f"[DRY RUN] Would merge with existing tenant: {tenant_name}")
                        else:
                            self._merge_tenant_data(existing_tenant, tenant_data, results, tenant_name)
                        imported_count += 1
                else:
                    # New tenant - create it
                    if dry_run:
                        results.append(f"[DRY RUN] Would create new tenant: {tenant_name}")
                    else:
                        self._create_tenant_from_backup(tenant_data, results, tenant_name)
                    imported_count += 1
                    
            except Exception as e:
                error_msg = f"❌ Error importing {tenant_name}: {str(e)}"
                results.append(error_msg)
                logger.error("BackupDataImportDialog", error_msg)
                error_count += 1
        
        # Save changes if not dry run
        if not dry_run:
            self.rent_tracker.save_tenants()
            
            # Recalculate delinquency if requested
            if self.recalc_checkbox.isChecked():
                results.append("\n🔄 Recalculating delinquency...")
                try:
                    self.rent_tracker.check_and_update_delinquency()
                    results.append("✅ Delinquency recalculation complete")
                except Exception as e:
                    results.append(f"⚠️  Warning: Delinquency recalculation failed: {e}")
        
        # Summary
        results.insert(0, f"\n{'='*50}")
        results.insert(0, f"Errors: {error_count}")
        results.insert(0, f"Skipped: {skipped_count}")
        results.insert(0, f"Imported: {imported_count}")
        results.insert(0, f"Total processed: {len(tenants_to_process)}")
        results.insert(0, f"{'DRY RUN - ' if dry_run else ''}Import Summary:")
        
        self.results_text.setPlainText('\n'.join(results))
        
        if not dry_run and imported_count > 0:
            self.data_imported.emit()
            QMessageBox.information(self, "Import Complete", 
                f"Successfully imported {imported_count} tenant(s).")
    
    def _create_tenant_from_backup(self, tenant_data: Dict, results: List[str], tenant_name: str):
        """Create a new tenant from backup data"""
        from src.tenant import Tenant
        
        # Extract rental period
        rental_period = tenant_data.get('rental_period')
        
        # Create tenant
        tenant = Tenant(
            name=tenant_name,
            rental_period=rental_period,
            rent_amount=tenant_data.get('rent_amount', 0.0),
            deposit_amount=tenant_data.get('deposit_amount', 0.0),
            contact_info=tenant_data.get('contact_info', {}),
            notes=tenant_data.get('notes', ''),
            delinquency_balance=tenant_data.get('delinquency_balance', 0.0),
            overpayment_credit=tenant_data.get('overpayment_credit', 0.0),
            rent_due_date=tenant_data.get('rent_due_date'),
            account_status=tenant_data.get('account_status', 'active'),
            service_credit=tenant_data.get('service_credit', 0.0),
            payment_history=tenant_data.get('payment_history', []),
            user_ids=[self.current_user_id] if self.current_user_id else []
        )
        
        # Add tenant
        self.rent_tracker.tenant_manager.add_tenant(tenant)
        
        payment_count = len(tenant_data.get('payment_history', []))
        results.append(f"✅ Created tenant: {tenant_name} with {payment_count} payment(s)")
        logger.info("BackupDataImportDialog", f"Created tenant from backup: {tenant_name}")
    
    def _merge_tenant_data(self, existing_tenant, backup_data: Dict, results: List[str], tenant_name: str):
        """Merge backup data with existing tenant"""
        merged_count = 0
        
        # Merge payment history
        backup_payments = backup_data.get('payment_history', [])
        existing_payment_dates = set()
        
        if hasattr(existing_tenant, 'payment_history'):
            for payment in existing_tenant.payment_history:
                # Create a unique key for each payment
                key = f"{payment.get('year')}-{payment.get('month')}-{payment.get('date')}-{payment.get('amount')}"
                existing_payment_dates.add(key)
        
        # Add payments that don't already exist
        for payment in backup_payments:
            key = f"{payment.get('year')}-{payment.get('month')}-{payment.get('date')}-{payment.get('amount')}"
            if key not in existing_payment_dates:
                if not hasattr(existing_tenant, 'payment_history'):
                    existing_tenant.payment_history = []
                existing_tenant.payment_history.append(payment)
                merged_count += 1
        
        # Update other fields if they're different
        if backup_data.get('notes') and backup_data['notes'] != existing_tenant.notes:
            # Append backup notes to existing notes
            if existing_tenant.notes:
                existing_tenant.notes += f"\n\n[From Backup {datetime.now().strftime('%Y-%m-%d')}]\n{backup_data['notes']}"
            else:
                existing_tenant.notes = backup_data['notes']
        
        results.append(f"✅ Merged with existing tenant: {tenant_name} (added {merged_count} payment(s))")
        logger.info("BackupDataImportDialog", f"Merged backup data with tenant: {tenant_name}, added {merged_count} payments")
