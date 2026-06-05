from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QCheckBox, QDoubleSpinBox, QPushButton, QMessageBox,
                             QComboBox, QSpinBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from assets.Logger import Logger

logger = Logger()

class MonthlyOverrideDialog(QDialog):
    def __init__(
        self,
        parent=None,
        current_rent=0.0,
        tenant_name="",
        rental_period=None,
        default_due_day=1,
        monthly_overrides=None,
        due_day_overrides=None,
        late_status_overrides=None,
    ):
        super().__init__(parent)
        logger.debug("MonthlyOverrideDialog", f"Initializing MonthlyOverrideDialog for {tenant_name}")
        self.current_rent = current_rent
        self.tenant_name = tenant_name
        self.rental_period = rental_period
        self.monthly_overrides = dict(monthly_overrides or {})
        self.due_day_overrides = dict(due_day_overrides or {})
        self.late_status_overrides = dict(late_status_overrides or {})
        try:
            normalized_due_day = int(default_due_day or 1)
        except Exception:
            normalized_due_day = 1
        self.default_due_day = min(max(normalized_due_day, 1), 31)
        self.setWindowTitle(f'Monthly Override - {tenant_name}')
        self.setFixedSize(540, 520)
        self.init_ui()

    def _coerce_date(self, raw_value):
        if not raw_value:
            return None

        if hasattr(raw_value, 'date'):
            try:
                return raw_value.date()
            except Exception:
                pass

        try:
            return datetime.fromisoformat(str(raw_value)).date()
        except Exception:
            return None

    def _shift_month(self, year, month, offset):
        total_months = ((int(year) * 12) + (int(month) - 1)) + int(offset)
        return total_months // 12, (total_months % 12) + 1

    def _populate_months(self):
        self.month_combo.clear()

        today = datetime.now().date()
        current_year = today.year
        current_month = today.month

        start_date = None
        end_date = None

        if isinstance(self.rental_period, dict):
            start_date = self._coerce_date(self.rental_period.get('start_date'))
            end_date = self._coerce_date(self.rental_period.get('end_date'))
        elif isinstance(self.rental_period, (list, tuple)) and len(self.rental_period) >= 2:
            start_date = self._coerce_date(self.rental_period[0])
            end_date = self._coerce_date(self.rental_period[1])

        if start_date is None:
            start_year, start_month = self._shift_month(current_year, current_month, -12)
        else:
            start_year, start_month = start_date.year, start_date.month

        if end_date is None:
            end_year, end_month = self._shift_month(current_year, current_month, 12)
        else:
            end_year, end_month = end_date.year, end_date.month
            if (end_year, end_month) < (current_year, current_month):
                end_year, end_month = current_year, current_month

        if (start_year, start_month) > (end_year, end_month):
            start_year, start_month = end_year, end_month

        display_month = datetime(start_year, start_month, 1)
        while (display_month.year, display_month.month) <= (end_year, end_month):
            self.month_combo.addItem(
                display_month.strftime('%B %Y'),
                f"{display_month.year:04d}-{display_month.month:02d}"
            )

            if display_month.month == 12:
                display_month = display_month.replace(year=display_month.year + 1, month=1)
            else:
                display_month = display_month.replace(month=display_month.month + 1)

    def _load_selected_month_settings(self):
        month_key = self.month_combo.currentData()
        if not month_key:
            return

        amount_override = self.monthly_overrides.get(month_key)
        self.rent_override_checkbox.setChecked(amount_override is not None)
        self.rent_input.setValue(float(amount_override if amount_override is not None else self.current_rent))
        self.rent_input.setEnabled(self.rent_override_checkbox.isChecked())

        due_day_override = self.due_day_overrides.get(month_key)
        self.due_day_override_checkbox.setChecked(due_day_override not in (None, ''))
        try:
            due_day_value = int(due_day_override) if due_day_override not in (None, '') else self.default_due_day
        except Exception:
            due_day_value = self.default_due_day
        self.due_day_input.setValue(min(max(due_day_value, 1), 31))
        self.due_day_input.setEnabled(self.due_day_override_checkbox.isChecked())

        late_status_override = str(self.late_status_overrides.get(month_key, 'auto') or 'auto').strip().lower()
        combo_index = self.late_status_combo.findData(late_status_override)
        if combo_index < 0:
            combo_index = self.late_status_combo.findData('auto')
        self.late_status_combo.setCurrentIndex(max(combo_index, 0))

        self.notes_input.clear()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f'Monthly Override for {self.tenant_name}')
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fd7e14; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Current rent display
        current_rent_label = QLabel(f'Regular Monthly Rent: ${self.current_rent:.2f}')
        current_rent_label.setStyleSheet("font-size: 14px; color: #6c757d; margin-bottom: 15px;")
        current_rent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(current_rent_label)
        
        # Month selection
        month_layout = QHBoxLayout()
        month_label = QLabel('Month:')
        month_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        
        self.month_combo = QComboBox()
        current_date = datetime.now()
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        self._populate_months()
        
        self.month_combo.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")
        
        month_layout.addWidget(month_label)
        month_layout.addWidget(self.month_combo)
        layout.addLayout(month_layout)

        layout.addSpacing(10)

        self.rent_override_checkbox = QCheckBox('Override rent amount for this month')
        self.rent_override_checkbox.setChecked(True)
        layout.addWidget(self.rent_override_checkbox)
        
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

        layout.addSpacing(10)

        self.due_day_override_checkbox = QCheckBox('Override due day for this month')
        self.due_day_override_checkbox.setChecked(False)
        layout.addWidget(self.due_day_override_checkbox)

        due_day_layout = QHBoxLayout()
        due_day_label = QLabel('Due Day Override:')
        due_day_label.setStyleSheet("font-weight: bold; min-width: 120px;")

        self.due_day_input = QSpinBox()
        self.due_day_input.setRange(1, 31)
        self.due_day_input.setValue(self.default_due_day)
        self.due_day_input.setEnabled(False)
        self.due_day_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")

        due_day_layout.addWidget(due_day_label)
        due_day_layout.addWidget(self.due_day_input)
        layout.addLayout(due_day_layout)

        layout.addSpacing(10)

        late_status_layout = QHBoxLayout()
        late_status_label = QLabel('Late Status Override:')
        late_status_label.setStyleSheet("font-weight: bold; min-width: 120px;")

        self.late_status_combo = QComboBox()
        self.late_status_combo.addItem('Automatic', 'auto')
        self.late_status_combo.addItem('Treat fully paid month as on-time', 'on_time')
        self.late_status_combo.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #dee2e6; border-radius: 4px;")

        late_status_layout.addWidget(late_status_label)
        late_status_layout.addWidget(self.late_status_combo)
        layout.addLayout(late_status_layout)
        
        layout.addSpacing(15)
        
        # Notes section
        notes_label = QLabel('Reason for Override:')
        notes_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Enter reason for this monthly override (e.g., partial month, maintenance, etc.)...")
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
                background-color: #fd7e14;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e8690a;
            }
            QPushButton:pressed {
                background-color: #dc6308;
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
        self.rent_override_checkbox.toggled.connect(self.rent_input.setEnabled)
        self.due_day_override_checkbox.toggled.connect(self.due_day_input.setEnabled)
        self.month_combo.currentIndexChanged.connect(self._load_selected_month_settings)
        self._load_selected_month_settings()
    
    def remove_override(self):
        """Handle remove override request"""
        selected_month = self.month_combo.currentText()
        reply = QMessageBox.question(self, "Remove Override", 
            f"Remove all monthly overrides for {selected_month}?\n\nThis clears the rent, due day, and late-status overrides for that month.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.remove_requested = True
            self.accept()
    
    def accept(self):
        """Validate and accept the dialog"""
        if not self.remove_requested:
            override_amount = self.rent_input.value()
            if self.rent_override_checkbox.isChecked() and override_amount < 0:
                QMessageBox.warning(self, "Invalid Amount", "Please enter a valid override amount (cannot be negative).")
                return

            has_active_override = (
                self.rent_override_checkbox.isChecked()
                or self.due_day_override_checkbox.isChecked()
                or self.late_status_combo.currentData() != 'auto'
            )
            if not has_active_override:
                QMessageBox.warning(self, "No Overrides Selected", "Select at least one override or use Remove Override.")
                return
            
            notes = self.notes_input.toPlainText().strip()
            if not notes:
                reply = QMessageBox.question(self, "No Reason", 
                    "No reason provided for override. Continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
        super().accept()
    
    def get_override_data(self):
        """Get the monthly override data from the dialog"""
        month_data = self.month_combo.currentData()  # "YYYY-MM" format
        override_amount = self.rent_input.value()
        notes = self.notes_input.toPlainText().strip()
        
        logger.debug("MonthlyOverrideDialog", f"Dialog data - month_data={month_data}, override_amount={override_amount}, notes='{notes}', remove_requested={self.remove_requested}")
        
        return {
            'month': month_data,
            'apply_rent_override': self.rent_override_checkbox.isChecked(),
            'override_amount': override_amount,
            'apply_due_day_override': self.due_day_override_checkbox.isChecked(),
            'due_day_override': self.due_day_input.value(),
            'late_status_override': self.late_status_combo.currentData(),
            'notes': notes,
            'remove_requested': self.remove_requested
        }
