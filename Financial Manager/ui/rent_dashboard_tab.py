from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QHBoxLayout, QPushButton, QComboBox, QMessageBox, QDialog
from PyQt6.QtGui import QFont, QColor, QBrush
from PyQt6.QtCore import Qt

# Set matplotlib backend before importing matplotlib components
import matplotlib
matplotlib.use('Qt5Agg')  # Ensure we use the correct backend for PyQt6
import matplotlib.pyplot as plt
plt.ioff()  # Turn off interactive mode to prevent issues

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import datetime
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from settings import SettingsController
from src.rent_tracker import RentTracker
from ui.create_tenant_dialog import CreateTenantDialog
from ui.tenant_details_dialog import TenantDetailsDialog
from ui.rent_management_tab import RentManagementTab
from assets.Logger import Logger

logger = Logger()

class RentDashboardTab(QWidget):
    from PyQt6.QtCore import pyqtSignal
    tenant_selected = pyqtSignal(object)  # Emits tenant object
    
    def __init__(self, current_user_id=None):
        super().__init__()
        logger.debug("RentDashboardTab", f"Initializing RentDashboardTab for user {current_user_id}")
    def __init__(self, current_user_id=None):
        super().__init__()
        self.current_user_id = current_user_id  # Store the current user ID
        self.apply_theme()
        self.rent_tracker = RentTracker(current_user_id)
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        title = QLabel('Rent Dashboard')
        title.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)
        # Create tenant button
        create_btn = QPushButton('Create New Tenant')
        create_btn.setStyleSheet('font-weight: bold; border-radius: 8px; padding: 10px 24px; background: #0078d4; color: #fff; font-size: 15px;')
        create_btn.clicked.connect(self.create_tenant)
        layout.addWidget(create_btn)
        # Sorting controls
        sort_layout = QHBoxLayout()
        sort_label = QLabel('Sort by:')
        sort_label.setFont(QFont('Segoe UI', 12))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Delinquency', 'Paid Up', 'Alphabetical'])
        self.sort_combo.currentIndexChanged.connect(self.update_table)
        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()
        layout.addLayout(sort_layout)
        # Search bar
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Search tenants by name...')
        self.search_edit.textChanged.connect(self.update_table)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        # Charts
        chart_layout = QHBoxLayout()
        try:
            # Create charts with proper error handling
            self.delinq_chart = FigureCanvas(Figure(figsize=(5, 4)))
            self.month_chart = FigureCanvas(Figure(figsize=(5, 4)))
            
            # Set proper parent for the canvas widgets
            self.delinq_chart.setParent(self)
            self.month_chart.setParent(self)
            
            chart_layout.addWidget(self.delinq_chart)
            chart_layout.addWidget(self.month_chart)
        except Exception as e:
            print(f"Error creating charts: {e}")
            # Create placeholder labels if chart creation fails
            chart_layout.addWidget(QLabel("Chart unavailable"))
            chart_layout.addWidget(QLabel("Chart unavailable"))
        
        layout.addLayout(chart_layout)
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['Name', 'Status', 'Rent Due', 'Delinquency', 'Deposit', 'Account'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet('font-size: 15px;')
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.update_table()
        self.rent_management_tab = None  # Will be set by main window
        self.table.cellDoubleClicked.connect(self.show_tenant_details)

    def apply_theme(self):
        settings = SettingsController()
        theme = settings.get_theme()
        if theme == 'dark':
            self.setStyleSheet('QWidget { background-color: #181818; color: #f0f0f0; } QTableWidget { background: #232323; color: #f0f0f0; } QHeaderView::section { background: #282828; color: #f0f0f0; }')
        elif theme == 'light':
            self.setStyleSheet('QWidget { background-color: #f8f8f8; color: #232323; } QTableWidget { background: #fff; color: #232323; } QHeaderView::section { background: #eaeaea; color: #232323; }')
        elif theme == 'blue':
            self.setStyleSheet('QWidget { background-color: #e3f2fd; color: #0d47a1; } QTableWidget { background: #bbdefb; color: #0d47a1; } QHeaderView::section { background: #90caf9; color: #0d47a1; }')
        elif theme == 'high-contrast':
            self.setStyleSheet('QWidget { background-color: #000; color: #fff; } QTableWidget { background: #222; color: #fff; } QHeaderView::section { background: #fff; color: #000; }')
        else:
            self.setStyleSheet('')

    def create_tenant(self):
        dialog = CreateTenantDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            new_tenant = self.rent_tracker.tenant_manager.add_tenant(
                name=data['name'],
                rental_period=data['rental_period'],
                rent_amount=data['rent_amount'],
                deposit_amount=data['deposit_amount'],
                contact_info=data['contact_info'],
                notes=data['notes'],
                rent_due_date=data['rent_due_date'],
                user_id=self.current_user_id
            )
            
            # Force delinquency calculation for the new tenant
            self.rent_tracker.check_and_update_delinquency()
            
            # Reload tenant data from disk to ensure all calculated fields are fresh
            self.rent_tracker.tenant_manager.load()
            
            # Update dashboard table
            self.update_table()
            
            # Refresh rent management tab dropdown if available
            if self.rent_management_tab and hasattr(self.rent_management_tab, 'refresh_tenant_dropdown'):
                self.rent_management_tab.refresh_tenant_dropdown()

    def update_table(self):
        tenants = self.rent_tracker.tenant_manager.list_tenants()
        # Filter to only show active tenants
        active_tenants = [t for t in tenants if getattr(t, 'account_status', 'Active') == 'Active']
        search_text = self.search_edit.text().strip().lower()
        filtered = [t for t in active_tenants if search_text in t.name.lower()]
        # Default sorting: delinquent first, else alphabetical
        sort_mode = self.sort_combo.currentText()
        if sort_mode == 'Delinquency':
            filtered.sort(key=lambda t: t.delinquency_balance, reverse=True)
            if not any(t.delinquency_balance > 0 for t in filtered):
                filtered.sort(key=lambda t: t.name.lower())
        elif sort_mode == 'Paid Up':
            filtered.sort(key=lambda t: t.total_rent_paid, reverse=True)
        elif sort_mode == 'Alphabetical':
            filtered.sort(key=lambda t: t.name.lower())
        # Always show delinquent accounts first (highlighted)
        self.table.setRowCount(len(filtered))
        for row, t in enumerate(filtered):
            is_delinquent = t.delinquency_balance > 0
            for col, val in enumerate([t.name, t.account_status, str(t.rent_amount), str(t.delinquency_balance), str(t.deposit_amount), t.tenant_id]):
                item = QTableWidgetItem(val)
                if is_delinquent:
                    item.setBackground(QBrush(QColor(255, 80, 80)))
                    item.setForeground(QBrush(QColor(255, 255, 255)))
                self.table.setItem(row, col, item)
        # Pass only active tenants to update_charts as well
        self.update_charts(active_tenants)

    def update_charts(self, tenants):
        # Filter to only show active tenants in charts
        active_tenants = [t for t in tenants if getattr(t, 'account_status', 'Active') == 'Active']
        
        # Delinquency vs total expected - only for months that are due (past + current)
        now = datetime.date.today()
        total_expected_due = 0
        total_delinq = sum(t.delinquency_balance for t in active_tenants)
        future_payment_credits = 0
        
        logger.debug("RentDashboardTab", f"Current date: {now.year}-{now.month}")
        
        # Calculate total expected rent only for months that are due + handle future payments
        for tenant in active_tenants:
            if hasattr(tenant, 'months_to_charge') and tenant.months_to_charge:
                for year, month in tenant.months_to_charge:
                    month_date = datetime.date(year, month, 1)
                    
                    # Only count months that are due (past and current month)
                    if month_date <= now:
                        effective_rent = self.rent_tracker.get_effective_rent(tenant, year, month)
                        total_expected_due += effective_rent
                        logger.debug("RentDashboardTab", f"Due month {year}-{month}: Tenant {tenant.name}, Expected=${effective_rent}")
                    
                    # Check for future payments (payments made to months not yet due)
                    elif month_date > now and hasattr(tenant, 'payment_history'):
                        future_payments = 0
                        for payment in tenant.payment_history:
                            if payment.get('year') == year and payment.get('month') == month:
                                future_payments += payment.get('amount', 0)
                        
                        if future_payments > 0:
                            # If there are future payments, include that month's expected rent
                            effective_rent = self.rent_tracker.get_effective_rent(tenant, year, month)
                            future_payment_credits += min(future_payments, effective_rent)
                            logger.debug("RentDashboardTab", f"Future payment: {year}-{month}, Tenant {tenant.name}, Payment=${future_payments}, Expected=${effective_rent}")
        
        # Adjust delinquency by future payment credits
        adjusted_delinq = max(total_delinq - future_payment_credits, 0)
        
        logger.debug("RentDashboardTab", f"Delinquency Chart: Total Expected Due=${total_expected_due}, Total Delinquent=${total_delinq}, Future Credits=${future_payment_credits}, Adjusted Delinq=${adjusted_delinq}")
        
        # Ensure non-negative values for pie chart (refunds can cause negative values)
        delinq_data = [max(adjusted_delinq, 0), max(total_expected_due - adjusted_delinq, 0)]
        delinq_labels = ['Delinquency', 'Paid/Expected']
        
        # Update delinquency chart with error handling
        try:
            if hasattr(self, 'delinq_chart') and self.delinq_chart:
                # Clear the figure completely and create a single subplot
                self.delinq_chart.figure.clear()
                ax1 = self.delinq_chart.figure.add_subplot(111)
                
                if sum(delinq_data) == 0:
                    ax1.text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=14)
                    ax1.set_title('Delinquency vs Expected (Due Months)', fontsize=12, pad=20)
                else:
                    # Create pie chart with better spacing
                    wedges, texts, autotexts = ax1.pie(delinq_data, labels=delinq_labels, autopct='%1.1f%%', 
                                                     colors=['#ff5050', '#0078d4'], startangle=90,
                                                     textprops={'fontsize': 10})
                    # Improve text positioning
                    for text in texts:
                        text.set_fontsize(10)
                    for autotext in autotexts:
                        autotext.set_fontsize(10)
                        autotext.set_color('white')
                        autotext.set_weight('bold')
                    
                    ax1.set_title(f'Delinquency vs Expected (Due Months)\n${adjusted_delinq:.0f} / ${total_expected_due:.0f}', 
                                 fontsize=12, pad=20)
                
                # Adjust layout to prevent text overlap
                self.delinq_chart.figure.tight_layout(pad=1.5)
                self.delinq_chart.draw()
        except Exception as e:
            logger.error("RentDashboardTab", f"Error updating delinquency chart: {e}")
        
        # Monthly paid vs expected - improved calculation
        month_expected = 0
        month_paid = 0
        
        logger.debug("RentDashboardTab", f"Calculating monthly chart for {now.year}-{now.month}")
        
        for tenant in active_tenants:
            # Check if this tenant should be charged for current month
            # Note: months_to_charge contains [year, month] lists, not (year, month) tuples
            should_charge = False
            if hasattr(tenant, 'months_to_charge'):
                for month_entry in tenant.months_to_charge:
                    if len(month_entry) >= 2 and month_entry[0] == now.year and month_entry[1] == now.month:
                        should_charge = True
                        break
            
            if should_charge:
                # Get effective rent for this month (considering overrides)
                effective_rent = self.rent_tracker.get_effective_rent(tenant, now.year, now.month)
                month_expected += effective_rent
                
                # Calculate actual payments for this month
                actual_paid = 0
                if hasattr(tenant, 'payment_history'):
                    for payment in tenant.payment_history:
                        if payment.get('year') == now.year and payment.get('month') == now.month:
                            actual_paid += payment.get('amount', 0)
                
                # Cap the "paid toward expected" at the expected amount for this tenant
                # Overpayments don't count toward other tenants' obligations
                paid_toward_expected = min(actual_paid, effective_rent)
                month_paid += paid_toward_expected
                
                logger.debug("RentDashboardTab", f"Tenant {tenant.name}: Expected={effective_rent}, Actual Paid={actual_paid}, Counted Toward Expected={paid_toward_expected}")
        
        logger.debug("RentDashboardTab", f"Total: Expected={month_expected}, Paid={month_paid}")
        
        # Ensure non-negative values for pie chart (refunds can cause negative values)
        month_data = [max(month_paid, 0), max(month_expected - month_paid, 0)]
        month_labels = ['Paid', 'Outstanding']
        
        # Update monthly chart with error handling
        try:
            if hasattr(self, 'month_chart') and self.month_chart:
                # Clear the figure completely and create a single subplot
                self.month_chart.figure.clear()
                ax2 = self.month_chart.figure.add_subplot(111)
                
                if sum(month_data) == 0:
                    ax2.text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=14)
                    ax2.set_title('This Month: Paid vs Expected', fontsize=12, pad=20)
                else:
                    # Create pie chart with better spacing
                    wedges, texts, autotexts = ax2.pie(month_data, labels=month_labels, autopct='%1.1f%%', 
                                                     colors=['#0078d4', '#ffb300'], startangle=90,
                                                     textprops={'fontsize': 10})
                    # Improve text positioning
                    for text in texts:
                        text.set_fontsize(10)
                    for autotext in autotexts:
                        autotext.set_fontsize(10)
                        autotext.set_color('white')
                        autotext.set_weight('bold')
                    
                    ax2.set_title(f'This Month: Paid vs Expected\n${month_paid:.0f} / ${month_expected:.0f}', 
                                 fontsize=12, pad=20)
                
                # Adjust layout to prevent text overlap
                self.month_chart.figure.tight_layout(pad=1.5)
                self.month_chart.draw()
        except Exception as e:
            logger.error("RentDashboardTab", f"Error updating monthly chart: {e}")

    def refresh_charts(self):
        """Force refresh of entire dashboard - can be called from other tabs"""
        logger.debug("RentDashboardTab", "Refreshing entire dashboard - recalculating all tenant data")
        
        # First, recalculate all tenant balances and delinquency
        self.rent_tracker.check_and_update_delinquency()
        
        # Then refresh all dashboard components
        self.refresh_dashboard()
    
    def refresh_dashboard(self):
        """Refresh all dashboard components with latest data"""
        # Get fresh tenant data after recalculation
        tenants = self.rent_tracker.tenant_manager.list_tenants()
        
        # Update the table with fresh data
        self.update_table()
        
        # Note: update_table() already calls update_charts(tenants) at the end

    def set_rent_management_tab(self, tab):
        self.rent_management_tab = tab

    def show_tenant_details(self, row, column):
        tenant_id = self.table.item(row, 5).text()
        tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
        if tenant and self.rent_management_tab:
            self.rent_management_tab.load_tenant(tenant)
            self.tenant_selected.emit(tenant)
            # Switch to rent management tab
            mw = self.window()
            if hasattr(mw, 'tabs'):
                for i in range(mw.tabs.count()):
                    if mw.tabs.widget(i) is self.rent_management_tab:
                        mw.tabs.setCurrentIndex(i)
                        break

    def closeEvent(self, event):
        """Cleanup when widget is closed"""
        try:
            if hasattr(self, 'delinq_chart') and self.delinq_chart:
                self.delinq_chart.deleteLater()
            if hasattr(self, 'month_chart') and self.month_chart:
                self.month_chart.deleteLater()
        except Exception as e:
            logger.error("RentDashboardTab", f"Error during cleanup: {e}")
        super().closeEvent(event)
