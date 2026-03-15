from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import datetime
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from assets.Logger import Logger

logger = Logger()

class TenantDashboard(QWidget):
    def __init__(self, rent_tracker=None):
        super().__init__()
        logger.debug("TenantDashboard", "Initializing TenantDashboard")
        self.rent_tracker = rent_tracker
        self.current_tenant = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the tenant dashboard UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Title section
        self.title_label = QLabel('Select a tenant to view dashboard')
        self.title_label.setFont(QFont('Segoe UI', 18, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #0056b3; margin-bottom: 10px;")
        main_layout.addWidget(self.title_label)
        
        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.content_layout = QVBoxLayout(scroll_widget)
        self.content_layout.setSpacing(20)
        
        # Charts container - will be populated when tenant is selected
        self.charts_container = QWidget()
        self.charts_layout = QVBoxLayout(self.charts_container)
        self.content_layout.addWidget(self.charts_container)
        
        # Initialize empty state
        self.show_empty_state()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
    
    def show_empty_state(self):
        """Show empty state when no tenant is selected"""
        # Clear existing charts
        self.clear_charts()
        
        empty_label = QLabel('📊 Select a tenant from the Rent Management tab to view detailed analytics')
        empty_label.setFont(QFont('Segoe UI', 14))
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("""
            color: #666666;
            background-color: #f8f9fa;
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            padding: 40px;
            margin: 20px;
        """)
        self.charts_layout.addWidget(empty_label)
    
    def clear_charts(self):
        """Clear all existing charts"""
        while self.charts_layout.count():
            child = self.charts_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def load_tenant(self, tenant):
        """Load tenant data and create dashboard"""
        if not tenant or not self.rent_tracker:
            self.show_empty_state()
            return
            
        self.current_tenant = tenant
        self.title_label.setText(f'Dashboard for {tenant.name}')
        
        # Clear existing content
        self.clear_charts()
        
        # Create tenant-specific charts
        self.create_tenant_charts()
    
    def create_tenant_charts(self):
        """Create all charts for the selected tenant"""
        if not self.current_tenant:
            return
        
        # Chart 1: Payment History Timeline (Last 12 months)
        self.create_payment_timeline_chart()
        
        # Chart 2: Monthly Rent vs Payments Comparison
        self.create_monthly_comparison_chart()
        
        # Chart 3: Balance Trend (Overpayment vs Delinquency over time)
        self.create_balance_trend_chart()
        
        # Chart 4: Payment Method Breakdown
        self.create_payment_method_chart()
    
    def create_payment_timeline_chart(self):
        """Create payment history timeline chart"""
        # Create chart frame
        frame = self.create_chart_frame("Payment History Timeline (Last 12 Months)")
        
        # Create matplotlib figure with proper size and tight layout
        fig = Figure(figsize=(10, 4), tight_layout=True)
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Get last 12 months of data
        now = datetime.date.today()
        months = []
        expected_amounts = []
        paid_amounts = []
        
        for i in range(11, -1, -1):  # Last 12 months
            month_date = datetime.date(now.year, now.month, 1) - datetime.timedelta(days=i*30)
            month_date = month_date.replace(day=1)  # First day of month
            
            year, month = month_date.year, month_date.month
            month_label = month_date.strftime('%b %Y')
            
            # Check if tenant was charged for this month
            expected = 0
            if hasattr(self.current_tenant, 'months_to_charge') and self.current_tenant.months_to_charge:
                for charge_year, charge_month in self.current_tenant.months_to_charge:
                    if charge_year == year and charge_month == month:
                        expected = self.rent_tracker.get_effective_rent(self.current_tenant, year, month)
                        break
            
            # Get actual payments for this month
            paid = 0
            if hasattr(self.current_tenant, 'payment_history'):
                for payment in self.current_tenant.payment_history:
                    if payment.get('year') == year and payment.get('month') == month:
                        paid += payment.get('amount', 0)
            
            months.append(month_label)
            expected_amounts.append(expected)
            paid_amounts.append(paid)
        
        # Create the chart
        x_pos = range(len(months))
        width = 0.35
        
        bars1 = ax.bar([x - width/2 for x in x_pos], expected_amounts, width, 
                      label='Expected Rent', color='#0078d4', alpha=0.8)
        bars2 = ax.bar([x + width/2 for x in x_pos], paid_amounts, width,
                      label='Payments Received', color='#28a745', alpha=0.8)
        
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount ($)')
        ax.set_title('Monthly Expected vs Received Payments')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(months, rotation=45)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Adjust layout with extra padding for titles and rotated labels
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.30, top=0.85)  # Extra space for labels and title
        frame.layout().addWidget(canvas)
        self.charts_layout.addWidget(frame)
    
    def create_monthly_comparison_chart(self):
        """Create monthly rent vs payments comparison chart"""
        frame = self.create_chart_frame("Current Year Monthly Comparison")
        
        fig = Figure(figsize=(10, 4), tight_layout=True)
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Get current year data
        now = datetime.date.today()
        current_year = now.year
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        expected_data = []
        paid_data = []
        
        for month in range(1, 13):
            # Check if tenant was charged for this month
            expected = 0
            if hasattr(self.current_tenant, 'months_to_charge') and self.current_tenant.months_to_charge:
                for charge_year, charge_month in self.current_tenant.months_to_charge:
                    if charge_year == current_year and charge_month == month:
                        expected = self.rent_tracker.get_effective_rent(self.current_tenant, current_year, month)
                        break
            
            # Get actual payments for this month
            paid = 0
            if hasattr(self.current_tenant, 'payment_history'):
                for payment in self.current_tenant.payment_history:
                    if payment.get('year') == current_year and payment.get('month') == month:
                        paid += payment.get('amount', 0)
            
            expected_data.append(expected)
            paid_data.append(paid)
        
        # Create line chart
        ax.plot(months, expected_data, marker='o', linewidth=2, markersize=6,
               label='Expected Rent', color='#0078d4')
        ax.plot(months, paid_data, marker='s', linewidth=2, markersize=6,
               label='Payments Received', color='#28a745')
        
        # Fill area between lines to show gaps
        ax.fill_between(months, expected_data, paid_data, alpha=0.3,
                       where=[p >= e for p, e in zip(paid_data, expected_data)],
                       color='green', label='Overpayment')
        ax.fill_between(months, expected_data, paid_data, alpha=0.3,
                       where=[p < e for p, e in zip(paid_data, expected_data)],
                       color='red', label='Shortfall')
        
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount ($)')
        ax.set_title(f'{current_year} Monthly Rent vs Payments')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Adjust layout with padding for title and labels
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.20, top=0.85)  # Extra space for title and labels
        frame.layout().addWidget(canvas)
        self.charts_layout.addWidget(frame)
    
    def create_balance_trend_chart(self):
        """Create balance trend chart showing overpayment credit vs delinquency"""
        frame = self.create_chart_frame("Balance Trend Analysis")
        
        fig = Figure(figsize=(10, 4), tight_layout=True)
        canvas = FigureCanvas(fig)
        
        # Create side-by-side subplots
        ax1 = fig.add_subplot(121)  # Current status pie
        ax2 = fig.add_subplot(122)  # Trend over time
        
        # Pie chart for current balance status
        current_overpayment = max(getattr(self.current_tenant, 'overpayment_credit', 0), 0)
        current_delinquency = max(getattr(self.current_tenant, 'delinquency_balance', 0), 0)
        current_rent = max(getattr(self.current_tenant, 'rent_amount', 0), 0)
        
        if current_overpayment > 0:
            pie_data = [current_overpayment]
            pie_labels = ['Overpayment Credit']
            colors = ['#28a745']
            title_text = f'Overpayment Credit: ${current_overpayment:.0f}'
        elif current_delinquency > 0:
            pie_data = [current_delinquency]
            pie_labels = ['Delinquency']
            colors = ['#dc3545']
            title_text = f'Delinquency: ${current_delinquency:.0f}'
        else:
            pie_data = [current_rent]
            pie_labels = ['Paid Up']
            colors = ['#28a745']
            title_text = 'Current Status: Paid Up'
        
        ax1.pie(pie_data, labels=pie_labels, autopct='%1.1f%%', colors=colors)
        ax1.set_title(title_text)
        
        # Balance trend line (simplified - could be enhanced with historical data)
        months = ['3 mo ago', '2 mo ago', '1 mo ago', 'Current']
        # For now, show simplified trend - in production you'd track historical balances
        balance_trend = [0, 0, current_delinquency/2 if current_delinquency > 0 else current_overpayment/2, 
                        current_delinquency if current_delinquency > 0 else current_overpayment]
        
        color = '#dc3545' if current_delinquency > 0 else '#28a745'
        ax2.plot(months, balance_trend, marker='o', linewidth=3, markersize=8, color=color)
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_ylabel('Balance ($)')
        ax2.set_title('Balance Trend')
        ax2.grid(True, alpha=0.3)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Adjust layout with generous padding for titles and labels
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.25, top=0.85)  # Extra space for titles and labels
        frame.layout().addWidget(canvas)
        self.charts_layout.addWidget(frame)
    
    def create_payment_method_chart(self):
        """Create payment method breakdown chart"""
        frame = self.create_chart_frame("Payment Method Analysis")
        
        fig = Figure(figsize=(10, 4), tight_layout=True)
        canvas = FigureCanvas(fig)
        
        # Create side-by-side subplots
        ax1 = fig.add_subplot(121)  # Payment method pie
        ax2 = fig.add_subplot(122)  # Payment frequency bar
        
        # Count payment methods
        payment_methods = {}
        total_amount = 0
        
        if hasattr(self.current_tenant, 'payment_history'):
            for payment in self.current_tenant.payment_history:
                method = payment.get('type', 'Unknown')
                amount = payment.get('amount', 0)
                
                if method in payment_methods:
                    payment_methods[method] += amount
                else:
                    payment_methods[method] = amount
                
                total_amount += amount
        
        if payment_methods:
            # Payment method pie chart
            methods = list(payment_methods.keys())
            amounts = list(payment_methods.values())
            
            # Filter out negative amounts (refunds) and their methods for pie chart
            # Pie charts can't display negative values
            positive_methods = []
            positive_amounts = []
            for method, amount in zip(methods, amounts):
                if amount > 0:
                    positive_methods.append(method)
                    positive_amounts.append(amount)
            
            if positive_amounts:
                colors = ['#0078d4', '#28a745', '#ffc107', '#dc3545', '#6f42c1'][:len(positive_methods)]
                ax1.pie(positive_amounts, labels=positive_methods, autopct='%1.1f%%', colors=colors)
                ax1.set_title('Payment Methods by Amount')
            else:
                ax1.text(0.5, 0.5, 'No Positive Payments', ha='center', va='center', fontsize=14)
                ax1.set_title('Payment Methods by Amount')
            
            # Payment frequency bar chart
            frequencies = [len([p for p in self.current_tenant.payment_history if p.get('type') == method]) 
                          for method in methods]
            
            bars = ax2.bar(methods, frequencies, color=colors)
            ax2.set_ylabel('Number of Payments')
            ax2.set_title('Payment Frequency by Method')
            
            # Fix matplotlib warning by setting ticks before labels
            ax2.set_xticks(range(len(methods)))
            ax2.set_xticklabels(methods, rotation=45)
            
            # Add value labels on bars
            for bar, freq in zip(bars, frequencies):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(freq)}', ha='center', va='bottom')
        else:
            # No payment data
            ax1.text(0.5, 0.5, 'No Payment Data', ha='center', va='center', fontsize=14)
            ax1.set_title('Payment Methods')
            ax2.text(0.5, 0.5, 'No Payment Data', ha='center', va='center', fontsize=14)
            ax2.set_title('Payment Frequency')
        
        # Adjust layout with generous padding for rotated labels and value annotations
        fig.tight_layout()
        fig.subplots_adjust(bottom=0.25, top=0.85)  # Extra space for titles and labels
        frame.layout().addWidget(canvas)
        self.charts_layout.addWidget(frame)
    
    def create_chart_frame(self, title):
        """Create a styled frame for charts"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setMinimumHeight(400)  # Set minimum height for proper chart display
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
                margin: 10px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Add title
        title_label = QLabel(title)
        title_label.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #0056b3; margin-bottom: 15px;")
        layout.addWidget(title_label)
        
        return frame

# Import matplotlib.pyplot for formatting
try:
    import matplotlib.pyplot as plt
except ImportError:
    pass
