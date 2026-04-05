from datetime import date

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)


class LateFeeDialog(QDialog):
    def __init__(self, parent=None, tenant_name="", config=None):
        super().__init__(parent)
        self.setWindowTitle(f"Late Fee Options - {tenant_name}")
        self.setMinimumWidth(520)

        cfg = config or {}

        layout = QVBoxLayout(self)

        config_group = QGroupBox("Late Fee Configuration")
        config_form = QFormLayout(config_group)

        self.enabled_checkbox = QCheckBox("Enable late fees")
        self.enabled_checkbox.setChecked(bool(cfg.get("enabled", False)))
        config_form.addRow("Enabled:", self.enabled_checkbox)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.0, 100000.0)
        self.amount_input.setDecimals(2)
        self.amount_input.setPrefix("$")
        self.amount_input.setValue(float(cfg.get("amount", 0.0) or 0.0))
        config_form.addRow("Late fee amount:", self.amount_input)

        self.basis_select = QComboBox()
        self.basis_select.addItems(["flat_amount", "percent_of_rent"])
        current_basis = str(cfg.get("fee_basis", "flat_amount") or "flat_amount").lower()
        self.basis_select.setCurrentText(current_basis if current_basis in ("flat_amount", "percent_of_rent") else "flat_amount")
        config_form.addRow("Fee basis:", self.basis_select)

        self.mode_select = QComboBox()
        self.mode_select.addItems(["fixed", "daily"])
        current_mode = str(cfg.get("mode", "fixed") or "fixed").lower()
        self.mode_select.setCurrentText(current_mode if current_mode in ("fixed", "daily") else "fixed")
        config_form.addRow("Fee mode:", self.mode_select)

        self.grace_days_input = QSpinBox()
        self.grace_days_input.setRange(0, 60)
        self.grace_days_input.setValue(int(cfg.get("grace_period_days", 0) or 0))
        config_form.addRow("Grace period days:", self.grace_days_input)

        self.use_start_date = QCheckBox("Use start date")
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat("yyyy-MM-dd")
        self.start_date_input.setDate(date.today())
        start_date = cfg.get("start_date")
        if start_date:
            self.use_start_date.setChecked(True)
            self.start_date_input.setDate(date.fromisoformat(start_date))
        config_form.addRow(self.use_start_date, self.start_date_input)

        self.use_end_date = QCheckBox("Use end date")
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDisplayFormat("yyyy-MM-dd")
        self.end_date_input.setDate(date.today())
        end_date = cfg.get("end_date")
        if end_date:
            self.use_end_date.setChecked(True)
            self.end_date_input.setDate(date.fromisoformat(end_date))
        config_form.addRow(self.use_end_date, self.end_date_input)

        layout.addWidget(config_group)

        action_group = QGroupBox("Action")
        action_form = QFormLayout(action_group)

        self.action_select = QComboBox()
        self.action_select.addItems([
            "save_config",
            "auto_apply_through_date",
            "manual_apply_month",
            "manual_remove_month",
            "remove_all_late_fees",
        ])
        action_form.addRow("Action:", self.action_select)

        self.through_date_input = QDateEdit()
        self.through_date_input.setCalendarPopup(True)
        self.through_date_input.setDisplayFormat("yyyy-MM-dd")
        self.through_date_input.setDate(date.today())
        action_form.addRow("Apply through date:", self.through_date_input)

        self.month_input = QLineEdit()
        self.month_input.setPlaceholderText("YYYY-MM")
        action_form.addRow("Target month:", self.month_input)

        self.override_amount_input = QDoubleSpinBox()
        self.override_amount_input.setRange(0.0, 100000.0)
        self.override_amount_input.setDecimals(2)
        self.override_amount_input.setPrefix("$")
        self.override_amount_input.setSpecialValueText("Use configured amount")
        self.override_amount_input.setValue(0.0)
        action_form.addRow("Override amount:", self.override_amount_input)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Optional notes")
        action_form.addRow("Notes:", self.notes_input)

        self.help_label = QLabel(
            "save_config: only saves settings | auto_apply_through_date: applies to overdue unpaid months | "
            "daily mode charges (days late after grace) x amount and records as Daily Late Fee | "
            "percent_of_rent basis treats value as percent of that month's effective rent | "
            "manual_apply_month/manual_remove_month: use YYYY-MM | remove_all_late_fees: removes all late fee entries"
        )
        self.help_label.setWordWrap(True)

        layout.addWidget(action_group)
        layout.addWidget(self.help_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        start_date = self.start_date_input.date().toString("yyyy-MM-dd") if self.use_start_date.isChecked() else None
        end_date = self.end_date_input.date().toString("yyyy-MM-dd") if self.use_end_date.isChecked() else None

        override_amount = self.override_amount_input.value()
        amount_override = override_amount if override_amount > 0 else None

        return {
            "enabled": self.enabled_checkbox.isChecked(),
            "amount": float(self.amount_input.value()),
            "fee_basis": self.basis_select.currentText().strip().lower(),
            "mode": self.mode_select.currentText().strip().lower(),
            "grace_period_days": int(self.grace_days_input.value()),
            "start_date": start_date,
            "end_date": end_date,
            "action": self.action_select.currentText(),
            "through_date": self.through_date_input.date().toString("yyyy-MM-dd"),
            "target_month": self.month_input.text().strip(),
            "override_amount": amount_override,
            "notes": self.notes_input.text().strip(),
        }
