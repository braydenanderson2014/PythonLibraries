from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QDoubleSpinBox, QPushButton, QMessageBox, QRadioButton,
                             QButtonGroup, QDateEdit, QTextEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from assets.Logger import Logger

logger = Logger()

class RentModificationDialog(QDialog):
    def __init__(self, parent=None, current_rent=0.0, tenant_name=""):
        super().__init__(parent)
        logger.debug("RentModificationDialog", f"Initializing RentModificationDialog for {tenant_name}")
        self.current_rent = current_rent
        self.tenant_name = tenant_name
        self.setWindowTitle(f'Modify Rent - {tenant_name}')
        self.setFixedSize(500, 420)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f'Modify Rent Amount for {self.tenant_name}')
        title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #0056b3; 
            margin-bottom: 20px;
            text-align: center;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current rent display
        current_rent_label = QLabel(f'Current Rent: ${self.current_rent:.2f}')
        current_rent_label.setStyleSheet("""
            font-size: 14px;
            color: #6c757d;
            text-align: center;
            margin-bottom: 15px;
        """)
        current_rent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(current_rent_label)
        
        # New rent amount
        rent_layout = QHBoxLayout()
        rent_label = QLabel('New Rent Amount:')
        rent_label.setStyleSheet("font-weight: bold; margin-right: 10px;")
        
        self.rent_input = QDoubleSpinBox()
        self.rent_input.setMaximum(100000)
        self.rent_input.setValue(self.current_rent)
        self.rent_input.setPrefix('$')
        self.rent_input.setStyleSheet("""
            padding: 8px; 
            font-size: 14px; 
            border: 1px solid #dee2e6; 
            border-radius: 4px;
            min-width: 120px;
        """)
        
        rent_layout.addWidget(rent_label)
        rent_layout.addWidget(self.rent_input)
        rent_layout.addStretch()
        layout.addLayout(rent_layout)
        
        layout.addSpacing(20)
        
        # Effective date options
        effective_label = QLabel('Effective Date:')
        effective_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(effective_label)
        
        self.date_group = QButtonGroup()
        
        # Apply from today
        self.today_radio = QRadioButton('Apply from today')
        self.today_radio.setChecked(True)
        self.today_radio.setStyleSheet("margin-bottom: 5px;")
        self.date_group.addButton(self.today_radio)
        layout.addWidget(self.today_radio)
        
        # Apply from specific date
        specific_layout = QHBoxLayout()
        self.specific_radio = QRadioButton('Apply from specific date:')
        self.specific_radio.setStyleSheet("margin-bottom: 5px;")
        self.date_group.addButton(self.specific_radio)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setEnabled(False)
        self.date_edit.setStyleSheet("""
            padding: 5px; 
            border: 1px solid #dee2e6; 
            border-radius: 4px;
            max-width: 120px;
        """)
        
        specific_layout.addWidget(self.specific_radio)
        specific_layout.addWidget(self.date_edit)
        specific_layout.addStretch()
        layout.addLayout(specific_layout)
        
        # Backdate to beginning of current month
        self.backdate_radio = QRadioButton('Backdate to beginning of current month')
        self.backdate_radio.setStyleSheet("margin-bottom: 10px;")
        self.date_group.addButton(self.backdate_radio)
        layout.addWidget(self.backdate_radio)
        
        # Connect radio button signals
        self.specific_radio.toggled.connect(self.date_edit.setEnabled)
        
        layout.addSpacing(20)
        
        # Notes section
        notes_label = QLabel('Notes (optional):')
        notes_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText('Enter any notes about this rent change...')
        self.notes_input.setStyleSheet("""
            border: 1px solid #dee2e6; 
            border-radius: 4px; 
            padding: 5px;
            font-size: 12px;
        """)
        layout.addWidget(self.notes_input)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton('APPLY CHANGES')
        apply_btn.clicked.connect(self.accept)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
        cancel_btn = QPushButton('CANCEL')
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
            QPushButton:pressed {
                background-color: #494f54;
            }
        """)
        
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_rent_data(self):
        """Get the rent modification data"""
        new_rent = self.rent_input.value()
        notes = self.notes_input.toPlainText().strip()
        
        # Determine effective date
        if self.today_radio.isChecked():
            effective_date = QDate.currentDate()
            date_type = 'today'
        elif self.specific_radio.isChecked():
            effective_date = self.date_edit.date()
            date_type = 'specific'
        else:  # backdate_radio
            # First day of current month
            current_date = QDate.currentDate()
            effective_date = QDate(current_date.year(), current_date.month(), 1)
            date_type = 'backdate'
        
        return {
            'new_rent': new_rent,
            'effective_date': effective_date.toString('yyyy-MM-dd'),
            'date_type': date_type,
            'notes': notes
        }
    
    def accept(self):
        """Validate and accept the dialog"""
        new_rent = self.rent_input.value()
        if new_rent <= 0:
            QMessageBox.warning(self, "Invalid Rent", "Please enter a valid rent amount.")
            return
        
        super().accept()
