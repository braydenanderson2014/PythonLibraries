from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QDoubleSpinBox, QPushButton, QMessageBox, 
                             QTextEdit, QGroupBox, QSizePolicy, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
from assets.Logger import Logger

logger = Logger()

class DepositAmountDialog(QDialog):
    """Dialog for editing tenant deposit amount"""
    
    deposit_updated = pyqtSignal()  # Signal emitted when deposit is updated
    
    def __init__(self, parent=None, tenant=None, rent_tracker=None):
        super().__init__(parent)
        logger.debug("DepositAmountDialog", f"Initializing DepositAmountDialog for tenant {tenant.name if tenant else 'Unknown'}")
        self.tenant = tenant
        self.rent_tracker = rent_tracker
        
        self.setWindowTitle(f'Edit Deposit Amount - {tenant.name if tenant else "Unknown"}')
        self.setFixedSize(600, 500)
        self.init_ui()
        
        if tenant:
            self.load_tenant_data()
    
    def init_ui(self):
        logger.debug("DepositAmountDialog", "Initializing UI")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel(f'Edit Deposit Amount')
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0056b3; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Tenant Info
        if self.tenant:
            tenant_info = QLabel(f'Tenant: {self.tenant.name} (ID: {self.tenant.tenant_id})')
            tenant_info.setStyleSheet("font-size: 16px; color: #6c757d; margin-bottom: 15px;")
            tenant_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(tenant_info)
        
        # Deposit Information Group (form layout for stable alignment)
        deposit_group = QGroupBox("Deposit Information")
        deposit_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        deposit_form = QFormLayout()
        deposit_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        deposit_form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        deposit_form.setHorizontalSpacing(16)
        deposit_form.setVerticalSpacing(12)

        # Current deposit value (read-only label)
        self.current_deposit_value = QLabel("$0.00")
        self.current_deposit_value.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #003d82;
                background-color: #e3f2fd;
                padding: 6px 10px;
                border: 1px solid #9ec5fe;
                border-radius: 4px;
            }
        """)
        self.current_deposit_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_deposit_value.setMinimumHeight(32)
        self.current_deposit_value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        deposit_form.addRow("Current Deposit Amount:", self.current_deposit_value)

        # New deposit amount spinbox
        self.new_deposit_spin = QDoubleSpinBox()
        self.new_deposit_spin.setRange(0, 99999)
        self.new_deposit_spin.setPrefix("$")
        self.new_deposit_spin.setDecimals(2)
        self.new_deposit_spin.setMinimumHeight(40)
        self.new_deposit_spin.setStyleSheet("""
            QDoubleSpinBox {
                font-size: 20px;
                font-weight: bold;
                padding: 8px 10px;
                border: 2px solid #0056b3;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
            QDoubleSpinBox:focus {
                border-color: #007bff;
                background-color: #ffffff;
            }
        """)
        self.new_deposit_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        deposit_form.addRow("New Deposit Amount:", self.new_deposit_spin)

        deposit_group.setLayout(deposit_form)
        main_layout.addWidget(deposit_group)
        
        # Notes Group
        notes_group = QGroupBox("Change Notes")
        notes_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        notes_layout = QVBoxLayout()
        notes_layout.setSpacing(10)
        
        notes_label = QLabel("Reason for change (optional):")
        notes_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        notes_layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setMinimumHeight(80)
        self.notes_edit.setPlaceholderText("Enter reason for deposit change...")
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                font-size: 14px;
                padding: 10px;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QTextEdit:focus {
                border-color: #007bff;
            }
        """)
        notes_layout.addWidget(self.notes_edit)
        
        notes_group.setLayout(notes_layout)
        main_layout.addWidget(notes_group)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        save_btn = QPushButton('Update Deposit')
        save_btn.clicked.connect(self.save_deposit_change)
        save_btn.setMinimumHeight(50)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumHeight(50)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        btn_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
    
    def load_tenant_data(self):
        """Load existing tenant deposit data"""
        if not self.tenant:
            logger.debug("DepositAmountDialog", "No tenant provided to deposit dialog")
            self.current_deposit_value.setText("No tenant selected")
            self.new_deposit_spin.setValue(0.0)
            return

        # Get the deposit amount with proper error handling
        deposit_amount = 0.0
        try:
            raw = getattr(self.tenant, 'deposit_amount', None)
            if raw is None:
                logger.debug("DepositAmountDialog", "No deposit_amount found, using 0.0")
                self.tenant.deposit_amount = 0.0
                deposit_amount = 0.0
            else:
                deposit_amount = float(raw)
                logger.debug("DepositAmountDialog", f"Loaded deposit amount: {deposit_amount}")
        except (ValueError, TypeError) as e:
            logger.error("DepositAmountDialog", f"Error converting deposit amount: {e}")
            self.tenant.deposit_amount = 0.0
            deposit_amount = 0.0

        # Update the display
        deposit_text = f"${deposit_amount:.2f}"
        logger.debug("DepositAmountDialog", f"Setting display text to: {deposit_text}")
        self.current_deposit_value.setText(deposit_text)
        self.new_deposit_spin.setValue(deposit_amount)
        logger.debug("DepositAmountDialog", f"Label now shows: '{self.current_deposit_value.text()}'")
        logger.debug("DepositAmountDialog", f"Spinbox value: {self.new_deposit_spin.value()}")
    
    def save_deposit_change(self):
        """Save the deposit amount change"""
        if not self.tenant or not self.rent_tracker:
            QMessageBox.warning(self, "Error", "No tenant or rent tracker available.")
            return
        
        new_deposit = self.new_deposit_spin.value()
        old_deposit = getattr(self.tenant, 'deposit_amount', 0)
        notes = self.notes_edit.toPlainText().strip()
        
        # Confirm the change
        if new_deposit == old_deposit:
            QMessageBox.information(self, "No Change", "The deposit amount hasn't changed.")
            return
        
        change_text = f"Change deposit from ${old_deposit:.2f} to ${new_deposit:.2f}"
        if notes:
            change_text += f"\nReason: {notes}"
        
        reply = QMessageBox.question(
            self, 
            'Confirm Deposit Change', 
            f'Are you sure you want to update the deposit amount?\n\n{change_text}',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Update tenant deposit amount
            self.tenant.deposit_amount = new_deposit
            
            # Log the change in tenant notes if notes provided
            if notes:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                change_log = f"\n[{timestamp}] Deposit changed from ${old_deposit:.2f} to ${new_deposit:.2f}. Reason: {notes}"
                
                if hasattr(self.tenant, 'notes') and self.tenant.notes:
                    self.tenant.notes += change_log
                else:
                    self.tenant.notes = change_log.strip()
            
            # Save tenant data
            self.rent_tracker.tenant_manager.update_tenant(self.tenant)
            
            QMessageBox.information(
                self, 
                "Success", 
                f"Deposit amount updated successfully!\n\nOld Amount: ${old_deposit:.2f}\nNew Amount: ${new_deposit:.2f}"
            )
            
            self.deposit_updated.emit()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update deposit amount: {str(e)}")
            logger.error("DepositAmountDialog", f"Failed to update deposit amount: {e}")
