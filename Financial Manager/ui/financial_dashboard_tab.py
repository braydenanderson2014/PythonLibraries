from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QFrame, QTableWidget, QTableWidgetItem,
                             QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Optional, List, Dict, Any
import matplotlib.pyplot as plt
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    try:
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas  # type: ignore
    except ImportError:
        FigureCanvas = None
from matplotlib.figure import Figure
from src.bank import Bank
from datetime import datetime, timedelta
import json
from assets.Logger import Logger

logger = Logger()

class FinancialDashboardTab(QWidget):
    def __init__(self, current_user_id=None):
        super().__init__()
        logger.debug("FinancialDashboardTab", f"Initializing FinancialDashboardTab for user {current_user_id}")
        self.current_user_id = current_user_id
        self.bank = Bank(current_user_id)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Financial Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Create scroll area for dashboard content
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Summary cards row
        summary_layout = QHBoxLayout()
        self.create_summary_cards(summary_layout)
        scroll_layout.addLayout(summary_layout)
        
        # Charts row
        charts_layout = QHBoxLayout()
        self.create_charts(charts_layout)
        scroll_layout.addLayout(charts_layout)
        
        # Upcoming payments section
        self.create_upcoming_payments_section(scroll_layout)
        
        # Late payments section
        self.create_late_payments_section(scroll_layout)
        
        # Recent transactions preview
        self.create_recent_transactions_section(scroll_layout)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        self.setLayout(layout)
        
    def create_summary_cards(self, layout):
        """Create summary cards showing key financial metrics"""
        self.summary_frame = QFrame()
        self.summary_frame.setFrameStyle(QFrame.Shape.Box)
        self.summary_frame.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        
        summary_layout = QHBoxLayout()
        
        # Get financial summary
        summary = self.bank.get_financial_summary(self.current_user_id)
        
        # Income card
        income_card = self.create_card("Total Income", f"${summary['total_income']:,.2f}", "#4CAF50")
        summary_layout.addWidget(income_card)
        
        # Expenses card
        expenses_card = self.create_card("Total Expenses", f"${summary['total_expenses']:,.2f}", "#F44336")
        summary_layout.addWidget(expenses_card)
        
        # Net balance card
        net_color = "#4CAF50" if summary['net_balance'] >= 0 else "#F44336"
        net_card = self.create_card("Net Balance", f"${summary['net_balance']:,.2f}", net_color)
        summary_layout.addWidget(net_card)
        
        # Number of transactions card
        transaction_count = len(self.bank.get_user_finances(self.current_user_id))
        transactions_card = self.create_card("Total Transactions", str(transaction_count), "#2196F3")
        summary_layout.addWidget(transactions_card)
        
        self.summary_frame.setLayout(summary_layout)
        layout.addWidget(self.summary_frame)
        
    def create_card(self, title, value, color):
        """Create a summary card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.Box)
        card.setStyleSheet(f"background-color: white; border: 2px solid {color}; border-radius: 10px; padding: 10px;")
        card.setMinimumHeight(80)
        
        card_layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; color: #666;")
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        card.setLayout(card_layout)
        
        return card
        
    def create_charts(self, layout):
        """Create financial charts"""
        if FigureCanvas is None:
            # Fallback when matplotlib backend is not available
            error_label = QLabel("Chart functionality not available - matplotlib backend missing")
            error_label.setStyleSheet("color: red; font-weight: bold; padding: 20px;")
            layout.addWidget(error_label)
            return
            
        # Income vs Expenses Chart
        self.income_expense_figure = Figure(figsize=(6, 4))
        self.income_expense_canvas = FigureCanvas(self.income_expense_figure)
        
        # Category Breakdown Chart
        self.category_figure = Figure(figsize=(6, 4))
        self.category_canvas = FigureCanvas(self.category_figure)
        
        layout.addWidget(self.income_expense_canvas)
        layout.addWidget(self.category_canvas)
        
        self.update_charts()
        
    def update_charts(self):
        """Update the financial charts"""
        summary = self.bank.get_financial_summary(self.current_user_id)
        
        # Income vs Expenses Pie Chart
        self.income_expense_figure.clear()
        if summary['total_income'] > 0 or summary['total_expenses'] > 0:
            ax1 = self.income_expense_figure.add_subplot(111)
            # Ensure non-negative values for pie chart
            income = max(summary['total_income'], 0)
            expenses = max(abs(summary['total_expenses']), 0)
            sizes = [income, expenses]
            labels = ['Income', 'Expenses']
            colors = ['#4CAF50', '#F44336']
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Income vs Expenses')
        
        # Category Breakdown Chart
        self.category_figure.clear()
        # Combine both income and expense categories
        all_categories = {}
        all_categories.update(summary['expense_by_category'])
        # Add income categories but don't include them in spending chart
        
        if all_categories:
            ax2 = self.category_figure.add_subplot(111)
            category_names = list(all_categories.keys())
            category_values = [abs(v) for v in all_categories.values()]
            ax2.bar(category_names, category_values)
            ax2.set_title('Spending by Category')
            ax2.tick_params(axis='x', rotation=45)
        
        self.income_expense_canvas.draw()
        self.category_canvas.draw()
        
    def create_upcoming_payments_section(self, layout):
        """Create section showing upcoming payments from recurring transactions"""
        section_label = QLabel("Upcoming Payments")
        section_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(section_label)
        
        self.upcoming_table = QTableWidget()
        self.upcoming_table.setColumnCount(5)
        self.upcoming_table.setHorizontalHeaderLabels(['Description', 'Amount', 'Due Date', 'Category', 'Account'])
        header = self.upcoming_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.upcoming_table.setMaximumHeight(200)
        
        layout.addWidget(self.upcoming_table)
        self.update_upcoming_payments()
        
    def create_late_payments_section(self, layout):
        """Create section showing overdue payments"""
        section_label = QLabel("Overdue Payments")
        section_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #F44336; margin-top: 20px;")
        layout.addWidget(section_label)
        
        self.late_table = QTableWidget()
        self.late_table.setColumnCount(6)
        self.late_table.setHorizontalHeaderLabels(['Description', 'Amount', 'Due Date', 'Days Late', 'Category', 'Account'])
        header = self.late_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.late_table.setMaximumHeight(150)
        
        layout.addWidget(self.late_table)
        self.update_late_payments()
        
    def create_recent_transactions_section(self, layout):
        """Create section showing recent transactions"""
        section_label = QLabel("Recent Transactions (Last 10)")
        section_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(section_label)
        
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(6)
        self.recent_table.setHorizontalHeaderLabels(['Date', 'Description', 'Amount', 'Type', 'Category', 'Account'])
        header = self.recent_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.recent_table.setMaximumHeight(250)
        
        layout.addWidget(self.recent_table)
        self.update_recent_transactions()
        
    def update_upcoming_payments(self):
        """Update the upcoming payments table"""
        try:
            recurring_transactions = self.bank.get_recurring_transactions()
            upcoming = []
            
            # Filter for user's recurring transactions and get upcoming ones
            for recurring in recurring_transactions:
                if recurring.user_id == self.current_user_id:
                    next_due = recurring.get_next_due_date()
                    if next_due and next_due <= datetime.now() + timedelta(days=30):  # Next 30 days
                        days_until = (next_due - datetime.now()).days
                        upcoming.append({
                            'description': recurring.desc,
                            'amount': recurring.amount,
                            'due_date': next_due,
                            'days_until': days_until,
                            'category': recurring.category,
                            'account': recurring.account,
                            'type': recurring.type_
                        })
            
            # Sort by due date
            upcoming.sort(key=lambda x: x['due_date'])
            
            self.upcoming_table.setRowCount(len(upcoming))
            for row, payment in enumerate(upcoming):
                self.upcoming_table.setItem(row, 0, QTableWidgetItem(payment['description']))
                amount_str = f"${payment['amount']:,.2f}"
                if payment['type'] == 'out':
                    amount_str = f"-{amount_str}"
                self.upcoming_table.setItem(row, 1, QTableWidgetItem(amount_str))
                self.upcoming_table.setItem(row, 2, QTableWidgetItem(payment['due_date'].strftime('%Y-%m-%d')))
                self.upcoming_table.setItem(row, 3, QTableWidgetItem(payment['category']))
                self.upcoming_table.setItem(row, 4, QTableWidgetItem(payment['account']))
                
        except Exception as e:
            logger.error("FinancialDashboardTab", f"Error updating upcoming payments: {e}")
            
    def update_late_payments(self):
        """Update the late payments table"""
        try:
            recurring_transactions = self.bank.get_recurring_transactions()
            late_payments = []
            
            # Find overdue recurring transactions
            for recurring in recurring_transactions:
                if recurring.user_id == self.current_user_id:
                    next_due = recurring.get_next_due_date()
                    if next_due and next_due < datetime.now():
                        days_late = (datetime.now() - next_due).days
                        late_payments.append({
                            'description': recurring.desc,
                            'amount': recurring.amount,
                            'due_date': next_due,
                            'days_late': days_late,
                            'category': recurring.category,
                            'account': recurring.account,
                            'type': recurring.type_
                        })
            
            # Sort by days late (most late first)
            late_payments.sort(key=lambda x: x['days_late'], reverse=True)
            
            self.late_table.setRowCount(len(late_payments))
            for row, payment in enumerate(late_payments):
                self.late_table.setItem(row, 0, QTableWidgetItem(payment['description']))
                amount_str = f"${payment['amount']:,.2f}"
                if payment['type'] == 'out':
                    amount_str = f"-{amount_str}"
                self.late_table.setItem(row, 1, QTableWidgetItem(amount_str))
                self.late_table.setItem(row, 2, QTableWidgetItem(payment['due_date'].strftime('%Y-%m-%d')))
                self.late_table.setItem(row, 3, QTableWidgetItem(f"{payment['days_late']} days"))
                self.late_table.setItem(row, 4, QTableWidgetItem(payment['category']))
                self.late_table.setItem(row, 5, QTableWidgetItem(payment['account']))
                
        except Exception as e:
            logger.error("FinancialDashboardTab", f"Error updating late payments: {e}")
            
    def update_recent_transactions(self):
        """Update the recent transactions table"""
        try:
            transactions = self.bank.get_user_finances(self.current_user_id)
            # Get last 10 transactions, sorted by date
            recent = sorted(transactions, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)[:10]
            
            self.recent_table.setRowCount(len(recent))
            for row, transaction in enumerate(recent):
                self.recent_table.setItem(row, 0, QTableWidgetItem(transaction['date']))
                self.recent_table.setItem(row, 1, QTableWidgetItem(transaction['desc']))
                amount_str = f"${transaction['amount']:,.2f}"
                if transaction['type'] == 'out':
                    amount_str = f"-{amount_str}"
                self.recent_table.setItem(row, 2, QTableWidgetItem(amount_str))
                self.recent_table.setItem(row, 3, QTableWidgetItem(transaction['type'].title()))
                self.recent_table.setItem(row, 4, QTableWidgetItem(transaction['category']))
                self.recent_table.setItem(row, 5, QTableWidgetItem(transaction['account']))
                
        except Exception as e:
            logger.error("FinancialDashboardTab", f"Error updating recent transactions: {e}")
    
    def set_current_user(self, user_id):
        """Set the current user and refresh the dashboard"""
        self.current_user_id = user_id
        self.bank.set_current_user(user_id)
        self.refresh_dashboard()
        
    def refresh_dashboard(self):
        """Refresh all dashboard components"""
        try:
            # Update summary cards
            summary_layout = self.summary_frame.layout()
            if summary_layout:
                for i in reversed(range(summary_layout.count())):
                    item = summary_layout.itemAt(i)
                    if item:
                        widget = item.widget()
                        if widget:
                            widget.setParent(None)
            self.create_summary_cards(summary_layout)
            
            # Update charts
            self.update_charts()
            
            # Update tables
            self.update_upcoming_payments()
            self.update_late_payments()
            self.update_recent_transactions()
            
        except Exception as e:
            logger.error("FinancialDashboardTab", f"Error refreshing dashboard: {e}")
