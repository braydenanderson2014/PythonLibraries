from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QDoubleSpinBox, QPushButton, QMessageBox, QSpinBox,
                             QTextEdit)
from PyQt6.QtCore import Qt
from datetime import datetime
from assets.Logger import Logger

logger = Logger()

class YearlyOverrideDialog(QDialog):
    def __init__(self, parent=None, current_rent=0.0, tenant_name=""):
        super().__init__(parent)
        logger.debug("YearlyOverrideDialog", f"Initializing YearlyOverrideDialog for {tenant_name}")
        self.current_rent = current_rent
        self.tenant_name = tenant_name
        self.setWindowTitle(f'Yearly Rent Override - {tenant_name}')
        self.setFixedSize(450, 300)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f'Yearly Rent Override for {self.tenant_name}')
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #6f42c1; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current rent display
        current_rent_label = QLabel(f'Regular Monthly Rent: ${self.current_rent:.2f}')
        current_rent_label.setStyleSheet("font-size: 14px; color: #6c757d; margin-bottom: 15px;")
        current_rent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(current_rent_label)
        
        # Year selection
        year_layout = QHBoxLayout()
        year_label = QLabel('Year:')
        year_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.year_spinner = QSpinBox()
        current_year = datetime.now().year
        # Allow backdating to 10 years ago and forward to 10 years in future
        self.year_spinner.setRange(current_year - 10, current_year + 10)
        self.year_spinner.setValue(current_year)
        self.year_spinner.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        year_layout.addWidget(year_label)
        year_layout.addWidget(self.year_spinner)
        layout.addLayout(year_layout)
        
        # Override amount
        rent_layout = QHBoxLayout()
        rent_label = QLabel('Override Amount:')
        rent_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.rent_input = QDoubleSpinBox()
        self.rent_input.setMinimum(0.0)  # Allow $0.00 values
        self.rent_input.setMaximum(100000)
        self.rent_input.setValue(self.current_rent)
        self.rent_input.setPrefix('$')
        self.rent_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        rent_layout.addWidget(rent_label)
        rent_layout.addWidget(self.rent_input)
        layout.addLayout(rent_layout)
        
        layout.addSpacing(15)
        
        # Info label
        info_label = QLabel('This will override the rent amount for all months in the selected year.')
        info_label.setStyleSheet("font-style: italic; color: #6c757d; font-size: 12px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        # Notes section
        notes_label = QLabel('Reason for Override:')
        notes_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Enter reason for this yearly override (e.g., rent increase, discount year, etc.)...")
        self.notes_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        layout.addWidget(self.notes_input)
        
        # Spacer
        layout.addStretch()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        apply_btn = QPushButton('Apply Override')
        apply_btn.clicked.connect(self.accept)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5d378a;
            }
            QPushButton:pressed {
                background-color: #543078;
            }
        """)
        
        remove_btn = QPushButton('Remove Override')
        remove_btn.clicked.connect(self.remove_override)
        remove_btn.setStyleSheet("""
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
        
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(remove_btn)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        self.remove_requested = False
    
    def remove_override(self):
        """Handle remove override request"""
        selected_year = self.year_spinner.value()
        reply = QMessageBox.question(self, "Remove Override", 
            f"Remove the yearly rent override for {selected_year}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.remove_requested = True
            self.accept()
    
    def accept(self):
        """Validate and accept the dialog"""
        if not self.remove_requested:
            override_amount = self.rent_input.value()
            if override_amount < 0:  # Allow $0.00 but not negative values
                QMessageBox.warning(self, "Invalid Amount", "Please enter a valid override amount (cannot be negative).")
                return
            
            notes = self.notes_input.toPlainText().strip()
            if not notes and override_amount != self.current_rent:
                reply = QMessageBox.question(self, "No Reason", 
                    "No reason provided for override. Continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
        super().accept()
    
    def get_override_data(self):
        """Get the yearly override data from the dialog"""
        year = self.year_spinner.value()
        override_amount = self.rent_input.value()
        notes = self.notes_input.toPlainText().strip()
        
        return {
            'year': year,
            'override_amount': override_amount,
            'notes': notes,
            'remove_requested': self.remove_requested
        }
