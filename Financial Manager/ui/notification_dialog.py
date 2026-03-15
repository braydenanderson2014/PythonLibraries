from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QComboBox, QPushButton, 
                             QDateEdit, QSpinBox, QGroupBox, QMessageBox, QFrame,
                             QScrollArea, QWidget, QSizePolicy, QCheckBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime, date
from src.notification_system import NotificationSystem
from assets.Logger import Logger

logger = Logger()

class NotificationDialog(QDialog):
    """Dialog for creating and managing notifications"""
    
    def __init__(self, parent=None, action_queue=None, rent_tracker=None):
        super().__init__(parent)
        logger.debug("NotificationDialog", "Initializing NotificationDialog")
        self.action_queue = action_queue
        self.rent_tracker = rent_tracker
        self.notification_system = NotificationSystem(action_queue, rent_tracker)
        
        self.setWindowTitle('Notification Manager')
        self.setFixedSize(800, 800)  # Increased height further to give more room for all sections
        self.init_ui()
    
    def init_ui(self):
        # Main layout for the dialog
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title (outside scroll area)
        title = QLabel('Notification Manager')
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0056b3; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFixedHeight(40)  # Fixed height for title
        main_layout.addWidget(title)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # Always show vertical scrollbar
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
        """)
        
        # Create content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Add all sections to the content layout
        self.create_test_section(content_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameStyle(QFrame.Shape.HLine | QFrame.Shadow.Sunken)
        separator.setStyleSheet("margin: 15px 0;")
        content_layout.addWidget(separator)
        
        # Manual notification section
        self.create_manual_section(content_layout)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameStyle(QFrame.Shape.HLine | QFrame.Shadow.Sunken)
        separator2.setStyleSheet("margin: 15px 0;")
        content_layout.addWidget(separator2)
        
        # Predefined templates section
        self.create_template_section(content_layout)
        
        # Separator
        separator3 = QFrame()
        separator3.setFrameStyle(QFrame.Shape.HLine | QFrame.Shadow.Sunken)
        separator3.setStyleSheet("margin: 15px 0;")
        content_layout.addWidget(separator3)
        
        # Daemon control section
        self.create_daemon_section(content_layout)
        
        # Add some extra spacing at the bottom to ensure scrolling
        content_layout.addSpacing(50)

        # Set the layout for the content widget
        content_widget.setLayout(content_layout)

        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)

        # Add scroll area to main layout (give it most of the space)
        main_layout.addWidget(scroll_area, 1)  # stretch factor of 1

        # Buttons (outside scroll area, always visible)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(10, 5, 10, 5)
        buttons_layout.addStretch()

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedHeight(35)  # Fixed height for button
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        buttons_layout.addWidget(close_btn)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)
    
    def create_test_section(self, layout):
        """Create test notification section"""
        test_group = QGroupBox("Test Notifications")
        test_group.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        test_layout = QVBoxLayout()
        
        # Test buttons
        test_buttons_layout = QHBoxLayout()
        
        test_normal_btn = QPushButton('Test Normal')
        test_normal_btn.clicked.connect(lambda: self.send_test_notification('normal'))
        test_normal_btn.setStyleSheet(self.get_button_style('#007bff', '#0056b3'))
        
        test_low_btn = QPushButton('Test Low Priority')
        test_low_btn.clicked.connect(lambda: self.send_test_notification('low'))
        test_low_btn.setStyleSheet(self.get_button_style('#28a745', '#1e7e34'))
        
        test_critical_btn = QPushButton('Test Critical')
        test_critical_btn.clicked.connect(lambda: self.send_test_notification('critical'))
        test_critical_btn.setStyleSheet(self.get_button_style('#dc3545', '#c82333'))
        
        test_buttons_layout.addWidget(test_normal_btn)
        test_buttons_layout.addWidget(test_low_btn)
        test_buttons_layout.addWidget(test_critical_btn)
        
        test_layout.addLayout(test_buttons_layout)
        
        # Status info
        status_info = QLabel("Test notifications to verify the system is working correctly.")
        status_info.setStyleSheet("color: #6c757d; font-size: 12px; margin-top: 5px;")
        test_layout.addWidget(status_info)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
    
    def create_manual_section(self, layout):
        """Create manual notification creation section"""
        manual_group = QGroupBox("Create Manual Notification")
        manual_group.setStyleSheet("QGroupBox { font-weight: bold; padding: 15px; }")
        manual_layout = QVBoxLayout()
        manual_layout.setSpacing(15)  # Increase spacing between elements
        
        # Title input
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter notification title...")
        self.title_input.setStyleSheet("padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.title_input.setMinimumHeight(35)  # Give title input more height
        title_layout.addWidget(self.title_input)
        manual_layout.addLayout(title_layout)
        
        # Add spacing after title
        manual_layout.addSpacing(10)
        
        # Message input
        manual_layout.addWidget(QLabel("Message:"))
        self.message_input = QTextEdit()
        # Use a reasonable minimum height and let the layout/scrollarea manage available space
        self.message_input.setMinimumHeight(96)
        self.message_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.message_input.setPlaceholderText("Enter notification message...")
        self.message_input.setStyleSheet("padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        manual_layout.addWidget(self.message_input)
        
        # Add more spacing after message input
        manual_layout.addSpacing(15)
        
        # Tenant selection for contact info
        tenant_layout = QHBoxLayout()
        tenant_layout.addWidget(QLabel("Send To Tenant:"))
        self.manual_tenant_combo = QComboBox()
        self.manual_tenant_combo.addItem("Select Tenant (optional)...", None)
        self.load_tenants_for_manual()
        self.manual_tenant_combo.setStyleSheet("padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        tenant_layout.addWidget(self.manual_tenant_combo)
        manual_layout.addLayout(tenant_layout)
        
        # Send method options
        manual_layout.addWidget(QLabel("Send Via:"))
        send_methods_layout = QHBoxLayout()
        
        self.send_system_check = QCheckBox("System Notification")
        self.send_system_check.setChecked(True)  # Default enabled
        send_methods_layout.addWidget(self.send_system_check)
        
        self.send_email_check = QCheckBox("Email")
        send_methods_layout.addWidget(self.send_email_check)
        
        self.send_sms_check = QCheckBox("SMS")
        send_methods_layout.addWidget(self.send_sms_check)
        
        manual_layout.addLayout(send_methods_layout)
        
        # Options row
        options_layout = QHBoxLayout()
        options_layout.setSpacing(15)  # Add spacing between options
        
        # Scheduled date
        options_layout.addWidget(QLabel("Send Date:"))
        self.scheduled_date = QDateEdit()
        self.scheduled_date.setDate(QDate.currentDate())
        self.scheduled_date.setCalendarPopup(True)
        self.scheduled_date.setStyleSheet("padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.scheduled_date.setMinimumHeight(35)  # Give options more height
        options_layout.addWidget(self.scheduled_date)
        
        # Urgency
        options_layout.addWidget(QLabel("Urgency:"))
        self.urgency_combo = QComboBox()
        self.urgency_combo.addItems(['normal', 'low', 'critical'])
        self.urgency_combo.setStyleSheet("padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        self.urgency_combo.setMinimumHeight(35)  # Give options more height
        options_layout.addWidget(self.urgency_combo)
        
        manual_layout.addLayout(options_layout)
        
        # Add spacing before queue button
        manual_layout.addSpacing(15)
        
        # Queue button
        queue_btn = QPushButton('Queue Notification')
        queue_btn.clicked.connect(self.queue_manual_notification)
        queue_btn.setStyleSheet(self.get_button_style('#28a745', '#1e7e34'))
        queue_btn.setMinimumHeight(40)  # Make button taller
        manual_layout.addWidget(queue_btn)
        
        manual_group.setLayout(manual_layout)
        layout.addWidget(manual_group)
    
    def load_tenants_for_manual(self):
        """Load tenants into the manual notification tenant combo box"""
        if not self.rent_tracker:
            return
        
        try:
            tenants = self.rent_tracker.tenant_manager.list_tenants()
            # Filter to only show active tenants
            active_tenants = [t for t in tenants if getattr(t, 'account_status', 'Active') == 'Active']
            for tenant in active_tenants:
                tenant_name = getattr(tenant, 'name', 'Unknown')
                tenant_id = getattr(tenant, 'tenant_id', None)
                
                if tenant_name and tenant_id:
                    display_text = f"{tenant_name} (ID: {tenant_id})"
                    self.manual_tenant_combo.addItem(display_text, tenant_id)
                    
        except Exception as e:
            logger.error("NotificationDialog", f"Failed to load tenants for manual notifications: {e}")
    
    
    def create_template_section(self, layout):
        """Create predefined template section"""
        template_group = QGroupBox("Quick Templates")
        template_group.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        template_layout = QVBoxLayout()
        
        # Template selection
        template_select_layout = QHBoxLayout()
        template_select_layout.addWidget(QLabel("Template:"))
        
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            'Custom',
            'Rent Due Reminder',
            'Lease Expiry Warning', 
            'Payment Overdue',
            'Maintenance Reminder',
            'General Reminder'
        ])
        self.template_combo.currentTextChanged.connect(self.on_template_changed)
        self.template_combo.setStyleSheet("padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        template_select_layout.addWidget(self.template_combo)
        template_layout.addLayout(template_select_layout)
        
        # Tenant selection for templates
        tenant_layout = QHBoxLayout()
        tenant_layout.addWidget(QLabel("Tenant:"))
        self.tenant_combo = QComboBox()
        self.tenant_combo.addItem("Select Tenant...")
        self.load_tenants()
        self.tenant_combo.setStyleSheet("padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        tenant_layout.addWidget(self.tenant_combo)
        template_layout.addLayout(tenant_layout)
        
        # Amount input for payment-related templates
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("Amount:"))
        self.amount_input = QSpinBox()
        self.amount_input.setRange(0, 99999)
        self.amount_input.setPrefix("$")
        self.amount_input.setStyleSheet("padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        amount_layout.addWidget(self.amount_input)
        
        # Due date for templates
        amount_layout.addWidget(QLabel("Due Date:"))
        self.template_date = QDateEdit()
        self.template_date.setDate(QDate.currentDate().addDays(30))
        self.template_date.setCalendarPopup(True)
        self.template_date.setStyleSheet("padding: 8px; border: 1px solid #dee2e6; border-radius: 4px;")
        amount_layout.addWidget(self.template_date)
        template_layout.addLayout(amount_layout)
        
        # Create from template button
        template_btn = QPushButton('Create from Template')
        template_btn.clicked.connect(self.create_from_template)
        template_btn.setStyleSheet(self.get_button_style('#17a2b8', '#138496'))
        template_layout.addWidget(template_btn)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
    
    def create_daemon_section(self, layout):
        """Create daemon control section"""
        daemon_group = QGroupBox("Notification Daemon")
        daemon_group.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        daemon_layout = QVBoxLayout()
        
        # Status display
        status = self.notification_system.get_daemon_status()
        status_text = f"Status: {'Running' if status['running'] else 'Stopped'}"
        status_text += f" | Check Interval: {status['check_interval']}s"
        status_text += f" | Plyer: {'Available' if status['plyer_available'] else 'Not Available'}"
        
        self.daemon_status_label = QLabel(status_text)
        self.daemon_status_label.setStyleSheet("color: #495057; font-size: 12px; margin-bottom: 10px;")
        daemon_layout.addWidget(self.daemon_status_label)
        
        # Control buttons
        daemon_buttons_layout = QHBoxLayout()
        
        start_daemon_btn = QPushButton('Start Daemon')
        start_daemon_btn.clicked.connect(self.start_daemon)
        start_daemon_btn.setStyleSheet(self.get_button_style('#28a745', '#1e7e34'))
        
        stop_daemon_btn = QPushButton('Stop Daemon')
        stop_daemon_btn.clicked.connect(self.stop_daemon)
        stop_daemon_btn.setStyleSheet(self.get_button_style('#dc3545', '#c82333'))
        
        refresh_status_btn = QPushButton('Refresh Status')
        refresh_status_btn.clicked.connect(self.refresh_daemon_status)
        refresh_status_btn.setStyleSheet(self.get_button_style('#6c757d', '#5a6268'))
        
        daemon_buttons_layout.addWidget(start_daemon_btn)
        daemon_buttons_layout.addWidget(stop_daemon_btn)
        daemon_buttons_layout.addWidget(refresh_status_btn)
        
        daemon_layout.addLayout(daemon_buttons_layout)
        daemon_group.setLayout(daemon_layout)
        layout.addWidget(daemon_group)
    
    def get_button_style(self, bg_color, hover_color):
        """Get button style with custom colors"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                padding: 10px 15px;
                font-size: 14px;
                border-radius: 5px;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """
    
    def load_tenants(self):
        """Load tenants into the combo box"""
        if not self.rent_tracker:
            return
        
        try:
            # Use list_tenants() method to get the actual Tenant objects
            tenants = self.rent_tracker.tenant_manager.list_tenants()
            # Filter to only show active tenants
            active_tenants = [t for t in tenants if getattr(t, 'account_status', 'Active') == 'Active']
            for tenant in active_tenants:
                # Handle both tenant objects and tenant dictionaries
                if hasattr(tenant, 'name'):
                    # Tenant object
                    tenant_name = tenant.name
                    tenant_id = getattr(tenant, 'tenant_id', tenant_name)
                elif isinstance(tenant, dict):
                    # Tenant dictionary
                    tenant_name = tenant.get('name', 'Unknown')
                    tenant_id = tenant.get('tenant_id', tenant_name)
                else:
                    # Fallback for string or other types
                    tenant_name = str(tenant)
                    tenant_id = tenant_name
                
                # Format display text to show both name and ID for clarity
                if tenant_name and tenant_name != 'Unknown':
                    if tenant_id and tenant_id != tenant_name:
                        display_text = f"{tenant_name} (ID: {tenant_id})"
                    else:
                        display_text = tenant_name
                else:
                    # Fallback to just ID if name is not available
                    display_text = f"Tenant {tenant_id}"
                
                self.tenant_combo.addItem(display_text, tenant_id)
                logger.debug("NotificationDialog", f"Added tenant: {display_text} with data: {tenant_id}")
                
        except Exception as e:
            logger.error("NotificationDialog", f"Failed to load tenants: {e}")
            # Add a fallback option
            self.tenant_combo.addItem("No tenants available", None)
    
    def send_test_notification(self, urgency):
        """Send a test notification"""
        try:
            success = self.notification_system.send_test_notification(urgency)
            if success:
                QMessageBox.information(self, 'Test Sent', f'Test notification ({urgency}) sent successfully!\n\nCheck your Windows notifications area.')
            else:
                QMessageBox.warning(self, 'Test Failed', 'Failed to send test notification. Check console for details.')
        except Exception as e:
            error_msg = f'Error sending test notification: {str(e)}'
            logger.error("NotificationDialog", error_msg)
            QMessageBox.critical(self, 'Error', error_msg)
    
    def queue_manual_notification(self):
        """Queue a manual notification"""
        title = self.title_input.text().strip()
        message = self.message_input.toPlainText().strip()
        
        if not title or not message:
            QMessageBox.warning(self, 'Missing Information', 'Please enter both title and message.')
            return
        
        # Get send methods
        send_methods = []
        if self.send_system_check.isChecked():
            send_methods.append("system")
        if self.send_email_check.isChecked():
            send_methods.append("email")
        if self.send_sms_check.isChecked():
            send_methods.append("sms")
        
        if not send_methods:
            QMessageBox.warning(self, 'No Send Method', 'Please select at least one send method.')
            return
        
        # Get tenant ID if selected
        tenant_id = self.manual_tenant_combo.currentData()
        
        # Validate contact requirements
        if tenant_id and ("email" in send_methods or "sms" in send_methods):
            contact_info = self.notification_system.get_tenant_contact_info(tenant_id)
            if "email" in send_methods and not contact_info.get('email'):
                reply = QMessageBox.question(
                    self, 
                    'Missing Email', 
                    'Selected tenant has no email address. Continue without email?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                else:
                    send_methods.remove("email")
            
            if "sms" in send_methods and not contact_info.get('phone'):
                reply = QMessageBox.question(
                    self, 
                    'Missing Phone', 
                    'Selected tenant has no phone number. Continue without SMS?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                else:
                    send_methods.remove("sms")
        
        try:
            scheduled_date = self.scheduled_date.date().toPyDate().strftime('%Y-%m-%d')
            urgency = self.urgency_combo.currentText()
            
            # Create action data with send methods
            action_data = {
                'title': title,
                'message': message,
                'urgency': urgency,
                'send_methods': send_methods,
                'notification_type': 'manual'
            }
            
            description = f"Manual notification: {title}"
            if tenant_id:
                tenant_name = self.get_tenant_name(tenant_id)
                description += f" (for {tenant_name})"
            description += f" via {', '.join(send_methods)}"
            
            action_id = self.action_queue.add_action(
                action_type='notification',
                scheduled_date=scheduled_date,
                tenant_id=tenant_id or 'system',
                action_data=action_data,
                description=description
            )
            
            QMessageBox.information(
                self, 
                'Notification Queued', 
                f'Notification queued successfully!\nAction ID: {action_id}\nScheduled for: {scheduled_date}\nSend methods: {", ".join(send_methods)}'
            )
            
            # Clear the form
            self.title_input.clear()
            self.message_input.clear()
            self.manual_tenant_combo.setCurrentIndex(0)
            self.send_system_check.setChecked(True)
            self.send_email_check.setChecked(False)
            self.send_sms_check.setChecked(False)
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to queue notification: {str(e)}')
    
    def get_tenant_name(self, tenant_id):
        """Get tenant name by ID"""
        if not self.rent_tracker or not tenant_id:
            return "Unknown"
        
        try:
            tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
            return getattr(tenant, 'name', 'Unknown') if tenant else "Unknown"
        except:
            return "Unknown"
    
    def on_template_changed(self, template_name):
        """Handle template selection change"""
        if template_name == 'Custom':
            return
        
        # Enable/disable fields based on template
        payment_templates = ['Rent Due Reminder', 'Payment Overdue']
        self.amount_input.setEnabled(template_name in payment_templates)
    
    def create_from_template(self):
        """Create notification from selected template"""
        template_name = self.template_combo.currentText()
        
        if template_name == 'Custom':
            QMessageBox.information(self, 'Template', 'Please select a specific template.')
            return
        
        tenant_text = self.tenant_combo.currentText()
        if tenant_text == "Select Tenant..." or tenant_text == "No tenants available":
            QMessageBox.warning(self, 'No Tenant', 'Please select a valid tenant for the template.')
            return
        
        try:
            tenant_id = self.tenant_combo.currentData()
            if tenant_id is None:
                tenant_id = tenant_text  # Fallback to tenant name
            
            # Extract just the tenant name from display text (remove ID part if present)
            if " (ID:" in tenant_text:
                tenant_name_only = tenant_text.split(" (ID:")[0]
            else:
                tenant_name_only = tenant_text
                
            amount = self.amount_input.value()
            due_date = self.template_date.date().toPyDate().strftime('%Y-%m-%d')
            
            # Map template names to notification types
            template_map = {
                'Rent Due Reminder': 'rent_due',
                'Lease Expiry Warning': 'lease_expiry',
                'Payment Overdue': 'payment_overdue',
                'Maintenance Reminder': 'maintenance_reminder',
                'General Reminder': 'general'
            }
            
            notification_type = template_map.get(template_name, 'general')
            
            # Create notification content using just the tenant name
            notification_content = self.notification_system.create_reminder_notification(
                reminder_type=notification_type,
                tenant_name=tenant_name_only,
                amount=amount if amount > 0 else None,
                due_date=due_date
            )
            
            # Fill in the manual form
            self.title_input.setText(notification_content['title'])
            self.message_input.setPlainText(notification_content['message'])
            
            QMessageBox.information(
                self, 
                'Template Applied', 
                'Template has been applied to the manual notification form. Review and queue when ready.'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to create from template: {str(e)}')
            logger.error("NotificationDialog", f"Template creation error: {e}")
    
    def start_daemon(self):
        """Start the notification daemon"""
        try:
            self.notification_system.start_daemon()
            QMessageBox.information(self, 'Daemon Started', 'Notification daemon has been started.')
            self.refresh_daemon_status()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to start daemon: {str(e)}')
    
    def stop_daemon(self):
        """Stop the notification daemon"""
        try:
            self.notification_system.stop_daemon()
            QMessageBox.information(self, 'Daemon Stopped', 'Notification daemon has been stopped.')
            self.refresh_daemon_status()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to stop daemon: {str(e)}')
    
    def refresh_daemon_status(self):
        """Refresh the daemon status display"""
        try:
            status = self.notification_system.get_daemon_status()
            status_text = f"Status: {'Running' if status['running'] else 'Stopped'}"
            status_text += f" | Check Interval: {status['check_interval']}s"
            status_text += f" | Plyer: {'Available' if status['plyer_available'] else 'Not Available'}"
            
            self.daemon_status_label.setText(status_text)
            
        except Exception as e:
            self.daemon_status_label.setText(f"Error getting status: {str(e)}")
