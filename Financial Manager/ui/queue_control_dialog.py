from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QComboBox, QPushButton, 
                             QDateEdit, QSpinBox, QGroupBox, QMessageBox, QFrame,
                             QScrollArea, QWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QTabWidget, QCheckBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime, date
from src.action_queue import ActionQueue
from assets.Logger import Logger

logger = Logger()

class QueueControlDialog(QDialog):
    """Dialog for managing the action queue system"""
    
    queue_updated = pyqtSignal()  # Signal emitted when queue is modified
    
    def __init__(self, parent=None, action_queue=None, rent_tracker=None):
        super().__init__(parent)
        logger.debug("QueueControlDialog", "Initializing QueueControlDialog")
        self.action_queue = action_queue
        self.rent_tracker = rent_tracker
        
        self.setWindowTitle('Queue Control Center')
        self.setFixedSize(900, 700)
        self.init_ui()
        self.refresh_queue_display()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel('Queue Control Center')
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0056b3; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Add Queue tab
        self.add_queue_tab = self.create_add_queue_tab()
        tab_widget.addTab(self.add_queue_tab, "Add to Queue")
        
        # View Queue tab
        self.view_queue_tab = self.create_view_queue_tab()
        tab_widget.addTab(self.view_queue_tab, "View Queue")
        
        main_layout.addWidget(tab_widget)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
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
        main_layout.addWidget(close_btn)
        
        self.setLayout(main_layout)
    
    def create_add_queue_tab(self):
        """Create the add to queue tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Tenant Selection
        tenant_group = QGroupBox("Select Tenant")
        tenant_layout = QVBoxLayout()
        
        self.tenant_combo = QComboBox()
        self.tenant_combo.addItem("Select Tenant...", None)
        self.load_tenants()
        tenant_layout.addWidget(self.tenant_combo)
        tenant_group.setLayout(tenant_layout)
        scroll_layout.addWidget(tenant_group)
        
        # Action Type Selection
        action_group = QGroupBox("Action Type")
        action_layout = QVBoxLayout()
        
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems([
            "notification",
            "rent_change", 
            "rental_period_change",
            "lease_expiry"
        ])
        self.action_type_combo.currentTextChanged.connect(self.on_action_type_changed)
        action_layout.addWidget(self.action_type_combo)
        action_group.setLayout(action_layout)
        scroll_layout.addWidget(action_group)
        
        # Scheduled Date
        date_group = QGroupBox("Scheduled Date")
        date_layout = QVBoxLayout()
        
        self.scheduled_date = QDateEdit()
        self.scheduled_date.setDate(QDate.currentDate())
        self.scheduled_date.setCalendarPopup(True)
        date_layout.addWidget(self.scheduled_date)
        date_group.setLayout(date_layout)
        scroll_layout.addWidget(date_group)
        
        # Dynamic fields container
        self.dynamic_fields_group = QGroupBox("Action Details")
        self.dynamic_fields_layout = QVBoxLayout()
        self.dynamic_fields_group.setLayout(self.dynamic_fields_layout)
        scroll_layout.addWidget(self.dynamic_fields_group)
        
        # Initialize with notification fields
        self.setup_notification_fields()
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.add_action_btn = QPushButton('Add to Queue')
        self.add_action_btn.clicked.connect(self.add_action_to_queue)
        self.add_action_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_layout.addWidget(self.add_action_btn)
        
        scroll_layout.addLayout(btn_layout)
        
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        widget.setLayout(layout)
        return widget
    
    def create_view_queue_tab(self):
        """Create the view queue tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Refresh button
        refresh_btn = QPushButton('Refresh Queue')
        refresh_btn.clicked.connect(self.refresh_queue_display)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        layout.addWidget(refresh_btn)
        
        # Queue table
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(6)
        self.queue_table.setHorizontalHeaderLabels([
            'Action Type', 'Tenant', 'Scheduled Date', 'Description', 'Status', 'Actions'
        ])
        
        # Set column widths
        header = self.queue_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.queue_table)
        
        widget.setLayout(layout)
        return widget
    
    def load_tenants(self):
        """Load tenants into the combo box"""
        if not self.rent_tracker:
            return
        
        try:
            tenants = self.rent_tracker.tenant_manager.list_tenants()
            for tenant in tenants:
                tenant_name = getattr(tenant, 'name', 'Unknown')
                tenant_id = getattr(tenant, 'tenant_id', None)
                
                if tenant_name and tenant_id:
                    display_text = f"{tenant_name} (ID: {tenant_id})"
                    self.tenant_combo.addItem(display_text, tenant_id)
                    
        except Exception as e:
            logger.error("QueueControlDialog", f"Failed to load tenants: {e}")
    
    def on_action_type_changed(self, action_type):
        """Handle action type change"""
        # Clear existing fields
        self.clear_dynamic_fields()
        
        # Setup fields based on action type
        if action_type == "notification":
            self.setup_notification_fields()
        elif action_type == "rent_change":
            self.setup_rent_change_fields()
        elif action_type == "rental_period_change":
            self.setup_rental_period_fields()
        elif action_type == "lease_expiry":
            self.setup_lease_expiry_fields()
    
    def clear_dynamic_fields(self):
        """Clear all dynamic fields"""
        for i in reversed(range(self.dynamic_fields_layout.count())):
            child = self.dynamic_fields_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
    
    def setup_notification_fields(self):
        """Setup notification-specific fields"""
        # Notification Type
        self.dynamic_fields_layout.addWidget(QLabel("Notification Type:"))
        self.notification_type_combo = QComboBox()
        self.notification_type_combo.addItems([
            "rent_due",
            "lease_expiry", 
            "payment_overdue",
            "maintenance_reminder",
            "general"
        ])
        self.dynamic_fields_layout.addWidget(self.notification_type_combo)
        
        # Message
        self.dynamic_fields_layout.addWidget(QLabel("Message:"))
        self.message_edit = QTextEdit()
        self.message_edit.setMaximumHeight(100)
        self.message_edit.setPlaceholderText("Enter notification message...")
        self.dynamic_fields_layout.addWidget(self.message_edit)
        
        # Urgency
        self.dynamic_fields_layout.addWidget(QLabel("Urgency:"))
        self.urgency_combo = QComboBox()
        self.urgency_combo.addItems(["normal", "low", "critical"])
        self.dynamic_fields_layout.addWidget(self.urgency_combo)
        
        # Send via
        self.dynamic_fields_layout.addWidget(QLabel("Send Via:"))
        send_layout = QHBoxLayout()
        
        self.send_email_check = QCheckBox("Email")
        self.send_sms_check = QCheckBox("SMS")
        self.send_system_check = QCheckBox("System Notification")
        self.send_system_check.setChecked(True)  # Default
        
        send_layout.addWidget(self.send_email_check)
        send_layout.addWidget(self.send_sms_check)
        send_layout.addWidget(self.send_system_check)
        
        send_widget = QWidget()
        send_widget.setLayout(send_layout)
        self.dynamic_fields_layout.addWidget(send_widget)
    
    def setup_rent_change_fields(self):
        """Setup rent change-specific fields"""
        self.dynamic_fields_layout.addWidget(QLabel("New Rent Amount:"))
        self.new_rent_spin = QSpinBox()
        self.new_rent_spin.setRange(0, 99999)
        self.new_rent_spin.setPrefix("$")
        self.dynamic_fields_layout.addWidget(self.new_rent_spin)
        
        self.dynamic_fields_layout.addWidget(QLabel("Notes:"))
        self.rent_notes_edit = QTextEdit()
        self.rent_notes_edit.setMaximumHeight(80)
        self.dynamic_fields_layout.addWidget(self.rent_notes_edit)
    
    def setup_rental_period_fields(self):
        """Setup rental period change fields"""
        self.dynamic_fields_layout.addWidget(QLabel("New Start Date:"))
        self.new_start_date = QDateEdit()
        self.new_start_date.setCalendarPopup(True)
        self.new_start_date.setDate(QDate.currentDate())
        self.dynamic_fields_layout.addWidget(self.new_start_date)
        
        self.dynamic_fields_layout.addWidget(QLabel("New End Date:"))
        self.new_end_date = QDateEdit()
        self.new_end_date.setCalendarPopup(True)
        self.new_end_date.setDate(QDate.currentDate().addYears(1))
        self.dynamic_fields_layout.addWidget(self.new_end_date)
        
        self.dynamic_fields_layout.addWidget(QLabel("Period Description:"))
        self.period_desc_edit = QLineEdit()
        self.period_desc_edit.setPlaceholderText("e.g. 12 months, 1 year")
        self.dynamic_fields_layout.addWidget(self.period_desc_edit)
    
    def setup_lease_expiry_fields(self):
        """Setup lease expiry fields"""
        self.dynamic_fields_layout.addWidget(QLabel("Expiry Notice:"))
        notice_label = QLabel("This will create a lease expiry reminder.")
        notice_label.setStyleSheet("color: #6c757d; font-style: italic;")
        self.dynamic_fields_layout.addWidget(notice_label)
        
        self.dynamic_fields_layout.addWidget(QLabel("Notes:"))
        self.expiry_notes_edit = QTextEdit()
        self.expiry_notes_edit.setMaximumHeight(80)
        self.dynamic_fields_layout.addWidget(self.expiry_notes_edit)
    
    def add_action_to_queue(self):
        """Add the configured action to the queue"""
        try:
            # Get tenant
            tenant_id = self.tenant_combo.currentData()
            if not tenant_id:
                QMessageBox.warning(self, "Missing Tenant", "Please select a tenant.")
                return
            
            # Get action type and scheduled date
            action_type = self.action_type_combo.currentText()
            scheduled_date = self.scheduled_date.date().toString('yyyy-MM-dd')
            
            # Build action data based on type
            if action_type == "notification":
                success = self.add_notification_action(tenant_id, scheduled_date)
            elif action_type == "rent_change":
                success = self.add_rent_change_action(tenant_id, scheduled_date)
            elif action_type == "rental_period_change":
                success = self.add_rental_period_action(tenant_id, scheduled_date)
            elif action_type == "lease_expiry":
                success = self.add_lease_expiry_action(tenant_id, scheduled_date)
            else:
                QMessageBox.warning(self, "Unknown Action", f"Unknown action type: {action_type}")
                return
            
            if success:
                QMessageBox.information(self, "Success", "Action added to queue successfully!")
                self.queue_updated.emit()
                self.refresh_queue_display()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add action to queue: {str(e)}")
            logger.error("QueueControlDialog", f"Failed to add action: {e}")
    
    def add_notification_action(self, tenant_id, scheduled_date):
        """Add notification action to queue"""
        notification_type = self.notification_type_combo.currentText()
        message = self.message_edit.toPlainText().strip()
        urgency = self.urgency_combo.currentText()
        
        if not message:
            QMessageBox.warning(self, "Missing Message", "Please enter a notification message.")
            return False
        
        # Build send methods
        send_methods = []
        if self.send_email_check.isChecked():
            send_methods.append("email")
        if self.send_sms_check.isChecked():
            send_methods.append("sms")
        if self.send_system_check.isChecked():
            send_methods.append("system")
        
        if not send_methods:
            QMessageBox.warning(self, "No Send Method", "Please select at least one send method.")
            return False
        
        action_data = {
            'notification_type': notification_type,
            'message': message,
            'urgency': urgency,
            'send_methods': send_methods
        }
        
        self.action_queue.add_notification(
            tenant_id=tenant_id,
            notification_date=scheduled_date,
            message=message,
            notification_type=notification_type
        )
        
        return True
    
    def add_rent_change_action(self, tenant_id, scheduled_date):
        """Add rent change action to queue"""
        new_rent = self.new_rent_spin.value()
        notes = self.rent_notes_edit.toPlainText().strip()
        
        if new_rent <= 0:
            QMessageBox.warning(self, "Invalid Rent", "Please enter a valid rent amount.")
            return False
        
        # Get current rent for reference
        tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
        old_rent = getattr(tenant, 'rent_amount', 0) if tenant else 0
        
        self.action_queue.add_rent_change(
            tenant_id=tenant_id,
            new_rent=new_rent,
            effective_date=scheduled_date,
            old_rent=old_rent,
            notes=notes
        )
        
        return True
    
    def add_rental_period_action(self, tenant_id, scheduled_date):
        """Add rental period change action to queue"""
        new_start = self.new_start_date.date().toString('yyyy-MM-dd')
        new_end = self.new_end_date.date().toString('yyyy-MM-dd')
        period_desc = self.period_desc_edit.text().strip()
        
        self.action_queue.add_rental_period_change(
            tenant_id=tenant_id,
            new_start_date=new_start,
            new_end_date=new_end,
            effective_date=scheduled_date,
            period_description=period_desc
        )
        
        return True
    
    def add_lease_expiry_action(self, tenant_id, scheduled_date):
        """Add lease expiry action to queue"""
        notes = self.expiry_notes_edit.toPlainText().strip()
        
        action_data = {
            'notes': notes
        }
        
        description = "Lease expiry reminder"
        if notes:
            description += f" - {notes}"
        
        self.action_queue.add_action(
            action_type='lease_expiry',
            scheduled_date=scheduled_date,
            tenant_id=tenant_id,
            action_data=action_data,
            description=description
        )
        
        return True
    
    def refresh_queue_display(self):
        """Refresh the queue display table"""
        if not self.action_queue:
            return
        
        try:
            actions = self.action_queue.get_all_actions()
            
            self.queue_table.setRowCount(len(actions))
            
            for row, action in enumerate(actions):
                # Action Type
                self.queue_table.setItem(row, 0, QTableWidgetItem(action.get('action_type', 'Unknown')))
                
                # Tenant Name
                tenant_id = action.get('tenant_id', '')
                tenant_name = self.get_tenant_name(tenant_id)
                self.queue_table.setItem(row, 1, QTableWidgetItem(tenant_name))
                
                # Scheduled Date
                scheduled_date = action.get('scheduled_date', '')
                self.queue_table.setItem(row, 2, QTableWidgetItem(scheduled_date))
                
                # Description
                description = action.get('description', '')
                self.queue_table.setItem(row, 3, QTableWidgetItem(description))
                
                # Status
                status = action.get('status', 'pending')
                status_item = QTableWidgetItem(status.title())
                if status == 'pending':
                    status_item.setBackground(Qt.GlobalColor.yellow)
                elif status == 'completed':
                    status_item.setBackground(Qt.GlobalColor.green)
                elif status == 'failed':
                    status_item.setBackground(Qt.GlobalColor.red)
                self.queue_table.setItem(row, 4, status_item)
                
                # Actions (Remove button)
                remove_btn = QPushButton('Remove')
                remove_btn.clicked.connect(lambda checked, action_id=action.get('action_id'): self.remove_action(action_id))
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        padding: 4px 8px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
                self.queue_table.setCellWidget(row, 5, remove_btn)
                
        except Exception as e:
            logger.error("QueueControlDialog", f"Failed to refresh queue display: {e}")
    
    def get_tenant_name(self, tenant_id):
        """Get tenant name by ID"""
        if not self.rent_tracker or not tenant_id:
            return "Unknown"
        
        try:
            tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
            return getattr(tenant, 'name', 'Unknown') if tenant else "Unknown"
        except:
            return "Unknown"
    
    def remove_action(self, action_id):
        """Remove an action from the queue"""
        if not action_id:
            return
        
        reply = QMessageBox.question(
            self, 
            'Confirm Removal', 
            'Are you sure you want to remove this action from the queue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.action_queue.remove_action(action_id)
                self.refresh_queue_display()
                self.queue_updated.emit()
                QMessageBox.information(self, "Success", "Action removed from queue.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove action: {str(e)}")
