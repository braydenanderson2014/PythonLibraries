from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QDateEdit, QTextEdit,
                             QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from assets.Logger import Logger

logger = Logger()

class RentQueryDialog(QDialog):
    def __init__(self, parent=None, rent_tracker=None, default_tenant_name=None):
        super().__init__(parent)
        logger.debug("RentQueryDialog", f"Initializing RentQueryDialog")
        self.rent_tracker = rent_tracker
        self.default_tenant_name = default_tenant_name
        self.setWindowTitle('Rent Query System - Test & Debug')
        self.setFixedSize(700, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Rent Query System')
        title.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #0056b3; 
            margin-bottom: 20px;
            text-align: center;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tenant selection
        tenant_layout = QHBoxLayout()
        tenant_label = QLabel('Tenant Name:')
        tenant_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.tenant_input = QComboBox()
        self.tenant_input.setEditable(True)
        self.tenant_input.setPlaceholderText("Select or enter tenant name...")
        
        # Populate with existing tenant names
        try:
            tenants = self.rent_tracker.tenant_manager.list_tenants()
            tenant_names = [t.name for t in tenants]
            self.tenant_input.addItems(tenant_names)
            
            # Set default tenant if provided, otherwise use first tenant
            if self.default_tenant_name and self.default_tenant_name in tenant_names:
                self.tenant_input.setCurrentText(self.default_tenant_name)
            elif tenant_names:
                self.tenant_input.setCurrentText(tenant_names[0])
        except Exception as e:
            self.tenant_input.addItem("Johnny Boy")  # Fallback
            if self.default_tenant_name:
                self.tenant_input.setCurrentText(self.default_tenant_name)
            
        self.tenant_input.setStyleSheet("""
            padding: 8px; 
            font-size: 14px; 
            border: 1px solid #dee2e6; 
            border-radius: 4px;
        """)
        
        tenant_layout.addWidget(tenant_label)
        tenant_layout.addWidget(self.tenant_input)
        layout.addLayout(tenant_layout)
        
        layout.addSpacing(10)
        
        # Query type selection
        query_type_layout = QHBoxLayout()
        query_type_label = QLabel('Query Type:')
        query_type_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.query_type = QComboBox()
        self.query_type.addItems(['Single Date', 'Date Range', 'Test Scenarios'])
        self.query_type.setStyleSheet("""
            padding: 8px; 
            font-size: 14px; 
            border: 1px solid #dee2e6; 
            border-radius: 4px;
        """)
        self.query_type.currentTextChanged.connect(self.on_query_type_changed)
        
        query_type_layout.addWidget(query_type_label)
        query_type_layout.addWidget(self.query_type)
        query_type_layout.addStretch()
        layout.addLayout(query_type_layout)
        
        layout.addSpacing(15)
        
        # Date inputs
        self.date_layout = QVBoxLayout()
        
        # Single date
        self.single_date_layout = QHBoxLayout()
        single_date_label = QLabel('Query Date:')
        single_date_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.single_date = QDateEdit()
        self.single_date.setDate(QDate.currentDate())
        self.single_date.setStyleSheet("""
            padding: 8px; 
            font-size: 14px; 
            border: 1px solid #dee2e6; 
            border-radius: 4px;
        """)
        
        self.single_date_layout.addWidget(single_date_label)
        self.single_date_layout.addWidget(self.single_date)
        self.single_date_layout.addStretch()
        
        # Date range
        self.date_range_layout = QVBoxLayout()
        
        start_layout = QHBoxLayout()
        start_label = QLabel('Start Date:')
        start_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.start_date = QDateEdit()
        current_date = QDate.currentDate()
        self.start_date.setDate(current_date.addMonths(-3))  # 3 months ago
        self.start_date.setStyleSheet("""
            padding: 8px; 
            font-size: 14px; 
            border: 1px solid #dee2e6; 
            border-radius: 4px;
        """)
        
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_date)
        start_layout.addStretch()
        
        end_layout = QHBoxLayout()
        end_label = QLabel('End Date:')
        end_label.setStyleSheet("font-weight: bold; min-width: 100px;")
        
        self.end_date = QDateEdit()
        self.end_date.setDate(current_date.addMonths(3))  # 3 months forward
        self.end_date.setStyleSheet("""
            padding: 8px; 
            font-size: 14px; 
            border: 1px solid #dee2e6; 
            border-radius: 4px;
        """)
        
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_date)
        end_layout.addStretch()
        
        self.date_range_layout.addLayout(start_layout)
        self.date_range_layout.addLayout(end_layout)
        
        # Add to main layout
        self.date_layout.addLayout(self.single_date_layout)
        self.date_layout.addLayout(self.date_range_layout)
        layout.addLayout(self.date_layout)
        
        # Initially hide date range
        self.hide_date_range()
        
        layout.addSpacing(15)
        
        # Query button
        query_btn = QPushButton('RUN QUERY')
        query_btn.clicked.connect(self.run_query)
        query_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        layout.addWidget(query_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(20)
        
        # Results display
        results_label = QLabel('Query Results:')
        results_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(results_label)
        
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setStyleSheet("""
            border: 1px solid #dee2e6; 
            border-radius: 4px; 
            padding: 10px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            background-color: #f8f9fa;
        """)
        layout.addWidget(self.results_display)
        
        # Close button
        close_btn = QPushButton('CLOSE')
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
            QPushButton:pressed {
                background-color: #494f54;
            }
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
    
    def on_query_type_changed(self, query_type):
        """Handle query type change"""
        if query_type == 'Single Date':
            self.show_single_date()
        elif query_type == 'Date Range':
            self.show_date_range()
        else:  # Test Scenarios
            self.hide_all_dates()
    
    def show_single_date(self):
        """Show single date input"""
        for i in range(self.single_date_layout.count()):
            widget = self.single_date_layout.itemAt(i).widget()
            if widget:
                widget.show()
        self.hide_date_range()
    
    def show_date_range(self):
        """Show date range inputs"""
        for i in range(self.date_range_layout.count()):
            item = self.date_range_layout.itemAt(i)
            if item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if widget:
                        widget.show()
        self.hide_single_date()
    
    def hide_single_date(self):
        """Hide single date input"""
        for i in range(self.single_date_layout.count()):
            widget = self.single_date_layout.itemAt(i).widget()
            if widget:
                widget.hide()
    
    def hide_date_range(self):
        """Hide date range inputs"""
        for i in range(self.date_range_layout.count()):
            item = self.date_range_layout.itemAt(i)
            if item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if widget:
                        widget.hide()
    
    def hide_all_dates(self):
        """Hide all date inputs"""
        self.hide_single_date()
        self.hide_date_range()
    
    def run_query(self):
        """Execute the selected query"""
        if not self.rent_tracker:
            self.results_display.setText("Error: No rent tracker available")
            return
        
        tenant_name = self.tenant_input.currentText().strip()
        if not tenant_name:
            QMessageBox.warning(self, "Missing Input", "Please enter a tenant name")
            return
        
        query_type = self.query_type.currentText()
        
        try:
            if query_type == 'Single Date':
                query_date = self.single_date.date().toString('yyyy-MM-dd')
                results = self.rent_tracker.query_rent_info(tenant_name, query_date)
                self.display_single_result(results)
                
            elif query_type == 'Date Range':
                start_date = self.start_date.date().toString('yyyy-MM-dd')
                end_date = self.end_date.date().toString('yyyy-MM-dd')
                results = self.rent_tracker.query_rent_timeline(tenant_name, start_date, end_date)
                self.display_timeline_results(results)
                
            else:  # Test Scenarios
                results = self.rent_tracker.test_rent_scenarios(tenant_name)
                self.display_test_results(results)
                
        except Exception as e:
            self.results_display.setText(f"Error running query: {str(e)}")
    
    def display_single_result(self, result):
        """Display single query result"""
        if not result:
            self.results_display.setText("No data found for the specified tenant and date.")
            return
        
        output = []
        output.append("=== SINGLE DATE QUERY ===")
        output.append("")
        output.append(f"Tenant: {result['tenant_name']}")
        output.append(f"Date: {result['date']} ({result['year_month'][1]:02d}/{result['year_month'][0]})")
        output.append("")
        
        output.append("--- RENT DETAILS ---")
        output.append(f"Base Rent: ${result['base_rent']:.2f}")
        output.append(f"Effective Rent: ${result['effective_rent']:.2f}")
        output.append(f"Final Rent: ${result['final_rent']:.2f}")
        
        if result['override_type']:
            output.append(f"Override: {result['override_type'].title()} (${result['override_amount']:.2f})")
        
        output.append("")
        output.append("--- PAYMENT ANALYSIS ---")
        output.append(f"Total Paid (This Month): ${result['total_paid']:.2f}")
        output.append(f"Balance Due (This Month): ${result['balance_due']:.2f}")
        output.append(f"Status: {result['payment_status']}")
        
        # Break down payment types
        if result.get('payment_details'):
            output.append("")
            output.append("Payment Breakdown:")
            cash_payments = result.get('cash_payments', 0.0)
            service_credit_used = result.get('service_credit_info', {}).get('used_this_month', 0.0)
            overpayment_used = result.get('overpayment_credit_info', {}).get('used_this_month', 0.0)
            
            if cash_payments > 0:
                output.append(f"  • Cash/Regular Payments: ${cash_payments:.2f}")
            if service_credit_used > 0:
                output.append(f"  • Service Credit Applied: ${service_credit_used:.2f}")
            if overpayment_used > 0:
                output.append(f"  • Overpayment Credit Applied: ${overpayment_used:.2f}")
            
            if not (cash_payments or service_credit_used or overpayment_used):
                output.append("  • No payments received this month")
            
            output.append("")
            output.append("Detailed Payment Records:")
            for payment in result['payment_details']:
                payment_date = payment.get('date', 'Unknown date')
                payment_type = payment.get('type', 'Unknown')
                amount = payment.get('amount', 0.0)
                is_credit = payment.get('is_credit_usage', False)
                credit_indicator = " (Credit Applied)" if is_credit else ""
                output.append(f"  • {payment_date}: ${amount:.2f} via {payment_type}{credit_indicator}")
        else:
            output.append("  • No payment details available")
        
        output.append("")
        output.append("--- CREDIT BALANCES ---")
        service_credit_info = result.get('service_credit_info', {})
        overpayment_info = result.get('overpayment_credit_info', {})
        
        output.append(f"Service Credit Balance: ${service_credit_info.get('current_balance', 0.0):.2f}")
        if service_credit_info.get('history_count', 0) > 0:
            output.append(f"  (Transaction History: {service_credit_info['history_count']} entries)")
        
        output.append(f"Overpayment Credit Balance: ${overpayment_info.get('current_balance', 0.0):.2f}")
        
        # Notification events
        notification_events = result.get('notification_events', [])
        if notification_events:
            output.append("")
            output.append("--- NOTIFICATION EVENTS ---")
            for notification in notification_events:
                status = notification.get('status', 'unknown')
                notif_type = notification.get('type', 'Unknown')
                urgency = notification.get('urgency', 'normal')
                message = notification.get('message', 'No message')
                
                status_indicator = "✓" if status == 'executed' else "⏳" if status == 'pending' else "?"
                urgency_indicator = " [HIGH]" if urgency == 'high' else " [CRITICAL]" if urgency == 'critical' else ""
                
                output.append(f"  {status_indicator} {notif_type}{urgency_indicator}")
                output.append(f"    Message: {message}")
                if notification.get('executed_date'):
                    output.append(f"    Executed: {notification['executed_date']}")
        else:
            output.append("")
            output.append("--- NOTIFICATION EVENTS ---")
            output.append("  • No notifications scheduled for this date")
        
        output.append("")
        output.append("--- TENANT FINANCIAL SUMMARY ---")
        output.append(f"Total Rent Paid (All Time): ${result.get('tenant_total_rent_paid', 0.0):.2f}")
        output.append(f"Total Service Credit Balance: ${result.get('tenant_total_service_credit', 0.0):.2f}")
        output.append(f"Total Overpayment Credits: ${result.get('tenant_total_overpayment', 0.0):.2f}")
        output.append(f"Delinquency Balance: ${result.get('tenant_total_delinquency', 0.0):.2f}")
        
        self.results_display.setText('\n'.join(output))
    
    def display_timeline_results(self, results):
        """Display timeline query results"""
        if not results:
            self.results_display.setText("No data found for the specified tenant and date range.")
            return
        
        output = []
        output.append("=== DATE RANGE TIMELINE ===")
        output.append("")
        
        # Store the first result to get tenant financial summary
        first_result = results[0] if results else None
        
        for result in results:
            output.append(f"Month: {result['date'].strftime('%B %Y')}")
            output.append(f"  Base Rent: ${result['base_rent']:.2f}")
            output.append(f"  Final Rent: ${result['final_rent']:.2f}")
            if result['override_type']:
                output.append(f"  Override: {result['override_type'].title()} (${result['override_amount']:.2f})")
            
            # Payment breakdown
            total_paid = result['total_paid']
            cash_payments = result.get('cash_payments', 0.0)
            service_credit_used = result.get('service_credit_info', {}).get('used_this_month', 0.0)
            overpayment_used = result.get('overpayment_credit_info', {}).get('used_this_month', 0.0)
            
            output.append(f"  Total Paid: ${total_paid:.2f}")
            if cash_payments > 0:
                output.append(f"    - Cash/Regular: ${cash_payments:.2f}")
            if service_credit_used > 0:
                output.append(f"    - Service Credit: ${service_credit_used:.2f}")
            if overpayment_used > 0:
                output.append(f"    - Overpayment Credit: ${overpayment_used:.2f}")
            
            output.append(f"  Balance Due: ${result['balance_due']:.2f}")
            output.append(f"  Status: {result['payment_status']}")
            
            # Notification events for this month
            notification_events = result.get('notification_events', [])
            if notification_events:
                output.append(f"  Notifications: {len(notification_events)} event(s)")
                for notification in notification_events:
                    status = "✓" if notification.get('status') == 'executed' else "⏳"
                    output.append(f"    {status} {notification.get('type', 'Unknown')}")
            
            output.append("-" * 50)
        
        # Add tenant financial summary at the end
        if first_result:
            output.append("")
            output.append("=== TENANT FINANCIAL SUMMARY ===")
            output.append(f"Total Rent Paid (All Time): ${first_result.get('tenant_total_rent_paid', 0.0):.2f}")
            output.append(f"Total Service Credit Balance: ${first_result.get('tenant_total_service_credit', 0.0):.2f}")
            output.append(f"Total Overpayment Credits: ${first_result.get('tenant_total_overpayment', 0.0):.2f}")
            output.append(f"Delinquency Balance: ${first_result.get('tenant_total_delinquency', 0.0):.2f}")
        
        self.results_display.setText('\n'.join(output))
    
    def display_test_results(self, results):
        """Display test scenario results"""
        if isinstance(results, str):
            self.results_display.setText(results)
            return
        
        output = []
        output.append(f"=== RENT SCENARIOS TEST FOR {results['tenant']} ===")
        output.append(f"Base Rent: ${results['base_rent']:.2f}")
        output.append("")
        
        # Store financial summary from first scenario with data
        tenant_summary = None
        
        for scenario in results['scenarios']:
            output.append(f"--- {scenario['scenario']} ({scenario['date']}) ---")
            info = scenario['info']
            if info:
                output.append(f"  Date: {info['date']} ({info['year_month'][1]:02d}/{info['year_month'][0]})")
                output.append(f"  Base Rent: ${info['base_rent']:.2f}")
                output.append(f"  Effective Rent: ${info['effective_rent']:.2f}")
                output.append(f"  Final Rent: ${info['final_rent']:.2f}")
                
                if info['override_type']:
                    output.append(f"  Override: {info['override_type'].title()} (${info['override_amount']:.2f})")
                
                output.append(f"  Total Paid: ${info['total_paid']:.2f}")
                output.append(f"  Balance Due: ${info['balance_due']:.2f}")
                output.append(f"  Status: {info['payment_status']}")
                
                # Capture tenant summary from first available result
                if not tenant_summary:
                    tenant_summary = info
            else:
                output.append("  No data available")
            output.append("")
        
        # Add tenant financial summary at the end
        if tenant_summary:
            output.append("=== TENANT FINANCIAL SUMMARY ===")
            output.append(f"Total Rent Paid (All Time): ${tenant_summary.get('tenant_total_rent_paid', 0.0):.2f}")
            output.append(f"Overpayment Credits: ${tenant_summary.get('tenant_total_overpayment', 0.0):.2f}")
            output.append(f"Delinquency Balance: ${tenant_summary.get('tenant_total_delinquency', 0.0):.2f}")
        
        self.results_display.setText('\n'.join(output))
