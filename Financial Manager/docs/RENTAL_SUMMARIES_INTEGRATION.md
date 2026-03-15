# Rental Summaries Integration Guide

## Overview

This guide explains how to integrate the Rental Summaries system into your Financial Manager application.

## Prerequisites

- Financial Manager application with RentTracker and TenantManager
- Python 3.6+
- Existing tenant and payment data

## Step 1: Add Imports to main_window.py

```python
# In main_window.py or relevant UI file

from src.rental_summaries import RentalSummaries
from src.rental_summaries_ui import RentalSummariesWidget
```

## Step 2: Initialize Summaries in MainWindow

```python
class MainWindow:
    def __init__(self):
        # ... existing initialization ...
        
        # Initialize rental summaries
        self.setup_rental_summaries()
    
    def setup_rental_summaries(self):
        """Initialize rental summaries system"""
        try:
            # Get existing rent_tracker instance (adjust path as needed)
            self.summaries_widget = RentalSummariesWidget(parent=self)
            self.summaries_widget.setup_summaries(self.rent_tracker)
            logger.info("MainWindow", "Rental summaries initialized")
        except Exception as e:
            logger.error("MainWindow", f"Failed to initialize summaries: {e}")
```

## Step 3: Add Menu Items

```python
def create_menu_bar(self):
    """Create menu bar with summaries options"""
    # ... existing menus ...
    
    # Add to View menu or create new Reports menu
    reports_menu = self.menuBar().addMenu("Reports")
    
    # Monthly summary
    reports_menu.addAction("Monthly Summary", self.show_monthly_summary)
    
    # Yearly summary
    reports_menu.addAction("Yearly Summary", self.show_yearly_summary)
    
    # Rental period summary
    reports_menu.addAction("Rental Period Summary", self.show_rental_period_summary)
    
    reports_menu.addSeparator()
    
    # Export options
    reports_menu.addAction("Export as JSON", self.export_as_json)
    reports_menu.addAction("Export as CSV", self.export_as_csv)
    reports_menu.addAction("Print Report", self.print_summary)
```

## Step 4: Implement Menu Actions

```python
def show_monthly_summary(self):
    """Show monthly summary dialog"""
    # Open tenant/date selection dialog
    tenant_id, year, month = self.show_date_selection_dialog("Select Month")
    
    if tenant_id:
        self.summaries_widget.action_show_monthly_summary(
            tenant_id, year, month
        )

def show_yearly_summary(self):
    """Show yearly summary dialog"""
    # Open tenant/year selection dialog
    tenant_id, year = self.show_year_selection_dialog("Select Year")
    
    if tenant_id:
        self.summaries_widget.action_show_yearly_summary(tenant_id, year)

def show_rental_period_summary(self):
    """Show rental period summary"""
    # Open tenant selection dialog
    tenant_id = self.show_tenant_selection_dialog("Select Tenant")
    
    if tenant_id:
        self.summaries_widget.action_show_rental_period_summary(tenant_id)

def export_as_json(self):
    """Export summary to JSON"""
    # Get user selection for summary type and tenant
    filepath = self.show_save_dialog("Save JSON", "*.json")
    
    if filepath:
        # Implementation based on user selection
        pass

def export_as_csv(self):
    """Export summary to CSV"""
    # Get user selection
    filepath = self.show_save_dialog("Save CSV", "*.csv")
    
    if filepath:
        # Implementation based on user selection
        pass

def print_summary(self):
    """Print summary"""
    # Get user selection
    tenant_id = self.show_tenant_selection_dialog("Select Tenant")
    
    if tenant_id:
        self.summaries_widget.action_print_rental_period_summary(tenant_id)
```

## Step 5: Create Selection Dialogs

### Tenant Selection Dialog

```python
def show_tenant_selection_dialog(self, title):
    """Show dialog to select a tenant"""
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton
    from PyQt6.QtCore import Qt
    
    dialog = QDialog(self)
    dialog.setWindowTitle(title)
    dialog.setGeometry(100, 100, 300, 150)
    
    layout = QVBoxLayout()
    
    # Get tenants
    tenants = self.tenant_manager.list_tenants()
    
    # Create combo box
    combo = QComboBox()
    for tenant in tenants:
        combo.addItem(tenant.name, tenant.tenant_id)
    
    layout.addWidget(combo)
    
    # Create buttons
    ok_btn = QPushButton("OK")
    ok_btn.clicked.connect(dialog.accept)
    layout.addWidget(ok_btn)
    
    dialog.setLayout(layout)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return combo.currentData()
    
    return None
```

### Date Selection Dialog

```python
def show_date_selection_dialog(self, title):
    """Show dialog to select date (year and month)"""
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QComboBox, \
                                QPushButton, QLabel
    
    dialog = QDialog(self)
    dialog.setWindowTitle(title)
    dialog.setGeometry(100, 100, 400, 150)
    
    layout = QVBoxLayout()
    
    # Tenant selection
    tenant_layout = QHBoxLayout()
    tenant_layout.addWidget(QLabel("Tenant:"))
    tenant_combo = QComboBox()
    tenants = self.tenant_manager.list_tenants()
    for tenant in tenants:
        tenant_combo.addItem(tenant.name, tenant.tenant_id)
    tenant_layout.addWidget(tenant_combo)
    layout.addLayout(tenant_layout)
    
    # Year selection
    year_layout = QHBoxLayout()
    year_layout.addWidget(QLabel("Year:"))
    year_combo = QComboBox()
    for year in range(2020, 2030):
        year_combo.addItem(str(year), year)
    year_layout.addWidget(year_combo)
    layout.addLayout(year_layout)
    
    # Month selection
    month_layout = QHBoxLayout()
    month_layout.addWidget(QLabel("Month:"))
    month_combo = QComboBox()
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    for i, month in enumerate(months, 1):
        month_combo.addItem(month, i)
    month_layout.addWidget(month_combo)
    layout.addLayout(month_layout)
    
    # Buttons
    btn_layout = QHBoxLayout()
    ok_btn = QPushButton("OK")
    cancel_btn = QPushButton("Cancel")
    
    ok_btn.clicked.connect(dialog.accept)
    cancel_btn.clicked.connect(dialog.reject)
    
    btn_layout.addWidget(ok_btn)
    btn_layout.addWidget(cancel_btn)
    layout.addLayout(btn_layout)
    
    dialog.setLayout(layout)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return (tenant_combo.currentData(), year_combo.currentData(), 
                month_combo.currentData())
    
    return None, None, None
```

## Step 6: Add Toolbar Buttons

```python
def create_toolbar(self):
    """Create toolbar with summary buttons"""
    # ... existing toolbar code ...
    
    toolbar = self.addToolBar("Reports")
    
    # Add summary buttons
    toolbar.addAction("Monthly", self.show_monthly_summary)
    toolbar.addAction("Yearly", self.show_yearly_summary)
    toolbar.addAction("Period", self.show_rental_period_summary)
    
    toolbar.addSeparator()
    
    # Add export buttons
    toolbar.addAction("Export JSON", self.export_as_json)
    toolbar.addAction("Export CSV", self.export_as_csv)
```

## Step 7: Batch Processing

For automatic report generation:

```python
def generate_all_tenant_reports(self):
    """Generate reports for all tenants"""
    from src.rental_summaries_ui import SummaryReportGenerator
    
    tenants = self.tenant_manager.list_tenants()
    output_dir = "reports"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create generator
    generator = SummaryReportGenerator(self.summaries_widget)
    
    # Generate reports
    results = generator.generate_rental_period_reports_for_all_tenants(output_dir)
    
    # Show results
    for result in results:
        status = "✓" if result['json'] and result['csv'] else "✗"
        print(f"{status} {result['tenant']}")
```

## Step 8: Settings and Configuration

### Add to settings.json

```json
{
  "rental_summaries": {
    "auto_generate": false,
    "auto_generate_interval": "weekly",
    "export_format": "both",
    "export_directory": "reports",
    "include_charts": true,
    "email_reports": false
  }
}
```

### Load Settings

```python
def load_summaries_settings(self):
    """Load summaries settings"""
    settings = self.load_settings()
    
    self.summaries_settings = settings.get('rental_summaries', {})
    
    # Apply settings
    if self.summaries_settings.get('auto_generate'):
        self.setup_auto_generation()
```

## Step 9: Testing

Run the validation tests:

```bash
python tests/test_rental_summaries.py
```

## Step 10: Documentation

- Place [RENTAL_SUMMARIES_GUIDE.md](RENTAL_SUMMARIES_GUIDE.md) in docs folder
- Place [RENTAL_SUMMARIES_QUICK_REF.md](RENTAL_SUMMARIES_QUICK_REF.md) in docs folder
- Add link to documentation in Help menu

## Complete Example Implementation

Here's a complete, minimal example:

```python
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import QTimer
from src.rental_summaries import RentalSummaries
from src.rental_summaries_ui import RentalSummariesWidget
from src.rent_tracker import RentTracker
from src.tenant import TenantManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.tenant_manager = TenantManager()
        self.rent_tracker = RentTracker(self.tenant_manager)
        
        # Initialize summaries
        self.summaries_widget = RentalSummariesWidget(parent=self)
        self.summaries_widget.setup_summaries(self.rent_tracker)
        
        # Setup UI
        self.setup_menus()
        self.setWindowTitle("Financial Manager with Rental Summaries")
        self.setGeometry(100, 100, 800, 600)
    
    def setup_menus(self):
        """Setup menu bar with rental summaries"""
        menu_bar = self.menuBar()
        reports_menu = menu_bar.addMenu("Reports")
        
        reports_menu.addAction(
            "Monthly Summary",
            self.show_monthly_summary
        )
        reports_menu.addAction(
            "Yearly Summary",
            self.show_yearly_summary
        )
        reports_menu.addAction(
            "Rental Period Summary",
            self.show_rental_period_summary
        )
    
    def show_monthly_summary(self):
        """Display monthly summary"""
        # For demo, use first tenant and January 2025
        tenants = self.tenant_manager.list_tenants()
        if tenants:
            self.summaries_widget.action_show_monthly_summary(
                tenants[0].tenant_id, 2025, 1
            )
        else:
            QMessageBox.warning(self, "No Data", "No tenants found")
    
    def show_yearly_summary(self):
        """Display yearly summary"""
        tenants = self.tenant_manager.list_tenants()
        if tenants:
            self.summaries_widget.action_show_yearly_summary(
                tenants[0].tenant_id, 2025
            )
        else:
            QMessageBox.warning(self, "No Data", "No tenants found")
    
    def show_rental_period_summary(self):
        """Display rental period summary"""
        tenants = self.tenant_manager.list_tenants()
        if tenants:
            self.summaries_widget.action_show_rental_period_summary(
                tenants[0].tenant_id
            )
        else:
            QMessageBox.warning(self, "No Data", "No tenants found")
```

## Troubleshooting Integration

### Issue: Import errors
**Solution:** Ensure paths in sys.path.append() are correct

### Issue: No data in summaries
**Solution:** Verify tenant has payment history and months_to_charge is set

### Issue: UI elements not showing
**Solution:** Check that summaries_widget is properly initialized before use

### Issue: Slow report generation
**Solution:** For large datasets, run batch generation on background thread

## Performance Optimization

For large-scale deployments:

```python
from PyQt6.QtCore import QThread, pyqtSignal

class ReportGenerationThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, summaries_widget, output_dir):
        super().__init__()
        self.summaries_widget = summaries_widget
        self.output_dir = output_dir
    
    def run(self):
        try:
            from src.rental_summaries_ui import SummaryReportGenerator
            generator = SummaryReportGenerator(self.summaries_widget)
            generator.generate_rental_period_reports_for_all_tenants(
                self.output_dir
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
```

## Next Steps

1. Integrate menu items and toolbar buttons
2. Run validation tests
3. Generate test reports
4. Deploy to production
5. Monitor performance and logs
6. Collect user feedback
7. Plan enhancements

## Support

For issues or questions, refer to:
- [RENTAL_SUMMARIES_GUIDE.md](RENTAL_SUMMARIES_GUIDE.md) - Full documentation
- [RENTAL_SUMMARIES_QUICK_REF.md](RENTAL_SUMMARIES_QUICK_REF.md) - Quick reference
- [RENTAL_SUMMARIES_IMPLEMENTATION.md](RENTAL_SUMMARIES_IMPLEMENTATION.md) - Implementation details
