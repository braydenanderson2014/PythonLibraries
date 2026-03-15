from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox, QPushButton, QMessageBox, QDateEdit, QTextEdit, QDoubleSpinBox, QFrame
from PyQt6.QtCore import Qt, QDate
from datetime import datetime, date
import calendar
from assets.Logger import Logger

logger = Logger()

class RenewLeaseDialog(QDialog):
    def __init__(self, parent=None, tenant=None):
        super().__init__(parent)
        logger.debug("RenewLeaseDialog", f"Initializing RenewLeaseDialog for tenant {tenant.name if tenant else 'Unknown'}")
        self.tenant = tenant
        self.setWindowTitle('Renew Lease')
        self.setFixedSize(800, 700)
        self.init_ui()
        
        if tenant:
            self.load_current_lease_info()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Renew Lease Agreement')
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0056b3; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current lease info section
        if self.tenant:
            self.create_current_lease_section(layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameStyle(QFrame.Shape.HLine | QFrame.Shadow.Sunken)
        separator.setStyleSheet("margin: 10px 0;")
        layout.addWidget(separator)
        
        # Extension period section
        period_layout = QHBoxLayout()
        period_label = QLabel('Extension Period:')
        period_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.period_spin = QSpinBox()
        self.period_spin.setMinimum(1)
        self.period_spin.setMaximum(60)
        self.period_spin.setValue(12)
        self.period_spin.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        self.period_unit = QComboBox()
        self.period_unit.addItems(['Months', 'Years'])
        self.period_unit.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.period_unit.currentTextChanged.connect(self.on_unit_changed)
        
        period_layout.addWidget(period_label)
        period_layout.addWidget(self.period_spin)
        period_layout.addWidget(self.period_unit)
        period_layout.addStretch()
        layout.addLayout(period_layout)
        
        # Start date section
        start_layout = QHBoxLayout()
        start_label = QLabel('New Period Starts:')
        start_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setMinimumWidth(200)
        calendar = self.start_date.calendarWidget()
        if calendar:
            calendar.setMinimumSize(300, 200)
        self.start_date.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_date)
        start_layout.addStretch()
        layout.addLayout(start_layout)
        
        # End date display (calculated)
        self.end_date_layout = QHBoxLayout()
        self.end_label = QLabel('New Period Ends:')
        self.end_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.end_date_display = QLabel()
        self.end_date_display.setStyleSheet("padding: 8px; font-size: 14px; color: #28a745; font-weight: bold;")
        
        self.end_date_layout.addWidget(self.end_label)
        self.end_date_layout.addWidget(self.end_date_display)
        self.end_date_layout.addStretch()
        layout.addLayout(self.end_date_layout)
        
        # Connect signals to update end date
        self.period_spin.valueChanged.connect(self.update_end_date)
        self.period_unit.currentTextChanged.connect(self.update_end_date)
        self.start_date.dateChanged.connect(self.update_end_date)
        
        # Rent adjustment section
        rent_section_label = QLabel('Rent Adjustment (Optional):')
        rent_section_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        layout.addWidget(rent_section_label)
        
        # Rent change explanation
        rent_explanation = QLabel('Note: Rent changes will be scheduled to take effect on the renewal start date.')
        rent_explanation.setStyleSheet("font-size: 12px; color: #6c757d; margin-left: 15px; margin-bottom: 10px;")
        layout.addWidget(rent_explanation)
        
        rent_layout = QHBoxLayout()
        
        # Current rent display
        current_rent_label = QLabel('Current Rent:')
        current_rent_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.current_rent_display = QLabel(f"${self.tenant.rent_amount:.2f}" if self.tenant else "$0.00")
        self.current_rent_display.setStyleSheet("padding: 8px; font-size: 14px; color: #6c757d;")
        
        rent_layout.addWidget(current_rent_label)
        rent_layout.addWidget(self.current_rent_display)
        rent_layout.addStretch()
        layout.addLayout(rent_layout)
        
        # New rent input
        new_rent_layout = QHBoxLayout()
        new_rent_label = QLabel('New Rent:')
        new_rent_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.new_rent_input = QDoubleSpinBox()
        self.new_rent_input.setMinimum(0.00)
        self.new_rent_input.setMaximum(99999.99)
        self.new_rent_input.setDecimals(2)
        self.new_rent_input.setPrefix("$")
        if self.tenant:
            self.new_rent_input.setValue(self.tenant.rent_amount)
        self.new_rent_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.new_rent_input.valueChanged.connect(self.on_rent_change)
        
        # Rent change indicator
        self.rent_change_label = QLabel()
        self.rent_change_label.setStyleSheet("padding: 8px; font-size: 12px; font-weight: bold;")
        
        new_rent_layout.addWidget(new_rent_label)
        new_rent_layout.addWidget(self.new_rent_input)
        new_rent_layout.addWidget(self.rent_change_label)
        new_rent_layout.addStretch()
        layout.addLayout(new_rent_layout)
        
        self.on_rent_change()  # Initialize rent change display
        
        # Notes section
        notes_label = QLabel('Renewal Notes (Optional):')
        notes_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Enter any notes about the lease renewal...")
        self.notes_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        layout.addWidget(self.notes_input)
        
        # Initial calculation
        self.update_end_date()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        # Renew button
        renew_btn = QPushButton('Renew Lease')
        renew_btn.clicked.connect(self.accept)
        renew_btn.setStyleSheet("""
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
                background-color: #494f54;
            }
        """)
        
        buttons_layout.addWidget(renew_btn)
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def create_current_lease_section(self, layout):
        """Create section showing current lease information"""
        current_section_label = QLabel('Current Lease Information:')
        current_section_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057; margin-bottom: 5px;")
        layout.addWidget(current_section_label)
        
        # Tenant name
        tenant_info = QLabel(f"Tenant: {self.tenant.name}")
        tenant_info.setStyleSheet("font-size: 13px; margin-left: 15px; color: #6c757d;")
        layout.addWidget(tenant_info)
        
        # Current lease dates
        if hasattr(self.tenant, 'rental_period') and self.tenant.rental_period:
            start_str = None
            end_str = None
            
            # Handle different rental_period formats
            if isinstance(self.tenant.rental_period, dict):
                start_str = self.tenant.rental_period.get('start_date')
                end_str = self.tenant.rental_period.get('end_date')
            elif isinstance(self.tenant.rental_period, (list, tuple)) and len(self.tenant.rental_period) >= 2:
                start_str = self.tenant.rental_period[0]
                end_str = self.tenant.rental_period[1]
            
            if start_str and end_str:
                start_date = datetime.strptime(start_str, '%Y-%m-%d').strftime('%B %d, %Y')
                end_date = datetime.strptime(end_str, '%Y-%m-%d').strftime('%B %d, %Y')
                
                current_period = QLabel(f"Current Period: {start_date} - {end_date}")
                current_period.setStyleSheet("font-size: 13px; margin-left: 15px; color: #6c757d;")
                layout.addWidget(current_period)
        
        # Current rent
        current_rent_info = QLabel(f"Current Rent: ${self.tenant.rent_amount:.2f}/month")
        current_rent_info.setStyleSheet("font-size: 13px; margin-left: 15px; color: #6c757d;")
        layout.addWidget(current_rent_info)
        
        # Account status
        status_color = "#28a745" if self.tenant.account_status.lower() == "active" else "#dc3545"
        status_info = QLabel(f"Status: {self.tenant.account_status.title()}")
        status_info.setStyleSheet(f"font-size: 13px; margin-left: 15px; color: {status_color}; font-weight: bold;")
        layout.addWidget(status_info)
    
    def on_rent_change(self):
        """Handle rent change to show increase/decrease"""
        if not self.tenant:
            return
        
        current_rent = self.tenant.rent_amount
        new_rent = self.new_rent_input.value()
        
        if new_rent == current_rent:
            self.rent_change_label.setText("(No change)")
            self.rent_change_label.setStyleSheet("padding: 8px; font-size: 12px; font-weight: bold; color: #6c757d;")
        elif new_rent > current_rent:
            increase = new_rent - current_rent
            percentage = (increase / current_rent) * 100
            self.rent_change_label.setText(f"(+${increase:.2f}, +{percentage:.1f}%)")
            self.rent_change_label.setStyleSheet("padding: 8px; font-size: 12px; font-weight: bold; color: #dc3545;")
        else:
            decrease = current_rent - new_rent
            percentage = (decrease / current_rent) * 100
            self.rent_change_label.setText(f"(-${decrease:.2f}, -{percentage:.1f}%)")
            self.rent_change_label.setStyleSheet("padding: 8px; font-size: 12px; font-weight: bold; color: #28a745;")
    
    def load_current_lease_info(self):
        """Load and display current lease information"""
        if not self.tenant:
            return
        
        # Try to determine current lease end from months_to_charge
        if hasattr(self.tenant, 'months_to_charge') and self.tenant.months_to_charge:
            # Find the last month in the rental period
            last_year = max(year for year, month in self.tenant.months_to_charge)
            last_month = max(month for year, month in self.tenant.months_to_charge if year == last_year)
            
            # Set start date to the month after current lease ends
            next_month = last_month + 1
            next_year = last_year
            if next_month > 12:
                next_month = 1
                next_year += 1
            
            self.start_date.setDate(QDate(next_year, next_month, 1))
    
    def on_unit_changed(self, unit):
        """Handle unit change between months and years"""
        current_value = self.period_spin.value()
        
        if unit == 'Years':
            # Convert to years, adjust range
            self.period_spin.setMaximum(5)
            if current_value > 5:
                self.period_spin.setValue(1)
        else:
            # Convert to months, adjust range  
            self.period_spin.setMaximum(60)
            if current_value <= 5:
                self.period_spin.setValue(12)
        
        self.update_end_date()
    
    def update_end_date(self):
        """Calculate and display the end date"""
        start_date = self.start_date.date().toPyDate()
        period = self.period_spin.value()
        unit = self.period_unit.currentText()
        
        if unit == 'Years':
            # Add years
            try:
                end_date = start_date.replace(year=start_date.year + period)
                # Subtract one day to get the last day of the lease
                from datetime import timedelta
                end_date = end_date - timedelta(days=1)
            except ValueError:
                # Handle leap year edge case
                end_date = start_date.replace(year=start_date.year + period, month=2, day=28)
        else:
            # Add months
            total_months = start_date.month + period
            end_year = start_date.year + (total_months - 1) // 12
            end_month = (total_months - 1) % 12 + 1
            
            # Get last day of the month
            last_day = calendar.monthrange(end_year, end_month)[1]
            end_date = date(end_year, end_month, last_day)
        
        self.end_date_display.setText(end_date.strftime('%B %d, %Y'))
        self.calculated_end_date = end_date
    
    def get_renewal_data(self):
        """Get the renewal data from the dialog"""
        start_date = self.start_date.date().toPyDate()
        period = self.period_spin.value()
        unit = self.period_unit.currentText()
        notes = self.notes_input.toPlainText().strip()
        new_rent = self.new_rent_input.value()
        
        return {
            'start_date': start_date,
            'end_date': self.calculated_end_date,
            'period': period,
            'unit': unit,
            'notes': notes,
            'new_rent': new_rent,
            'rent_changed': new_rent != self.tenant.rent_amount if self.tenant else False,
            'queue_rent_change': new_rent != self.tenant.rent_amount if self.tenant else False,
            'old_rent': self.tenant.rent_amount if self.tenant else 0.0
        }
