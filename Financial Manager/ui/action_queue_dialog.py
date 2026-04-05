from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, 
                             QMessageBox, QFrame, QTextEdit, QSpinBox, QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime

from assets.Logger import Logger
logger = Logger()
class ActionQueueDialog(QDialog):
    """Dialog to view and manage queued actions for a tenant"""
    
    def __init__(self, parent=None, action_queue=None, tenant=None, rent_tracker=None):
        super().__init__(parent)
        tenant_name = tenant.name if tenant else 'All Tenants'
        logger.debug("ActionQueueDialog", f"Initializing ActionQueueDialog for {tenant_name}")
        self.action_queue = action_queue
        self.tenant = tenant
        self.rent_tracker = rent_tracker
        self.setWindowTitle(f'Scheduled Actions - {tenant_name}')
        self.setFixedSize(900, 700)
        self.init_ui()
        self.load_actions()
        logger.info("ActionQueueDialog", f"ActionQueueDialog initialized for {tenant_name}")
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Scheduled Actions')
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0056b3; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tenant info
        if self.tenant:
            tenant_info = QLabel(f'Tenant: {self.tenant.name}')
            tenant_info.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(tenant_info)
        
        # Actions table
        self.actions_table = QTableWidget()
        self.actions_table.setColumnCount(6)
        self.actions_table.setHorizontalHeaderLabels([
            'Type', 'Description', 'Scheduled Date', 'Status', 'Created', 'Action'
        ])
        
        # Set column widths
        header = self.actions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Scheduled Date
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Status
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Created
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Action
        
        # Set a fixed width for the Action column to ensure buttons fit
        self.actions_table.setColumnWidth(5, 170)
        
        self.actions_table.setAlternatingRowColors(True)
        self.actions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Set row height to be 5 pixels bigger
        self.actions_table.verticalHeader().setDefaultSectionSize(35)
        
        self.actions_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.actions_table)
        
        # Action details
        details_label = QLabel('Action Details:')
        details_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(100)
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Select an action to view details...")
        self.details_text.setStyleSheet("padding: 8px; font-size: 12px; border: 1px solid #dee2e6; border-radius: 4px;")
        layout.addWidget(self.details_text)
        
        # Connect selection change
        self.actions_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        # Cleanup button
        cleanup_btn = QPushButton('Cleanup Old Actions')
        cleanup_btn.clicked.connect(self.show_cleanup_dialog)
        cleanup_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        
        refresh_btn = QPushButton('Refresh')
        refresh_btn.clicked.connect(self.load_actions)
        refresh_btn.setStyleSheet("""
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
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
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
        
        buttons_layout.addWidget(cleanup_btn)
        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_actions(self):
        """Load actions into the table"""
        logger.debug("ActionQueueDialog", "Loading actions into table")
        if not self.action_queue:
            logger.warning("ActionQueueDialog", "No action queue available")
            return
        
        # Get actions for tenant or all actions
        if self.tenant:
            actions = self.action_queue.get_tenant_actions(self.tenant.tenant_id)
            logger.debug("ActionQueueDialog", f"Loaded {len(actions)} actions for tenant {self.tenant.tenant_id}")
        else:
            actions = self.action_queue.actions
            logger.debug("ActionQueueDialog", f"Loaded {len(actions)} total actions")
        
        # Sort by scheduled date
        actions.sort(key=lambda x: x['scheduled_date'])
        
        self.actions_table.setRowCount(len(actions))
        
        for row, action in enumerate(actions):
            # Type
            type_item = QTableWidgetItem(action['action_type'].replace('_', ' ').title())
            if action['action_type'] == 'rent_change':
                type_item.setBackground(QColor(144, 238, 144))  # Light green
            elif action['action_type'] == 'notification':
                type_item.setBackground(QColor(173, 216, 230))  # Light blue
            elif action['action_type'] == 'payment_submission':
                type_item.setBackground(QColor(255, 239, 204))  # Light amber
            self.actions_table.setItem(row, 0, type_item)
            
            # Description
            desc_item = QTableWidgetItem(action['description'])
            self.actions_table.setItem(row, 1, desc_item)
            
            # Scheduled Date
            try:
                scheduled_date = datetime.strptime(action['scheduled_date'], '%Y-%m-%d')
                date_str = scheduled_date.strftime('%b %d, %Y')
            except:
                date_str = action['scheduled_date']
            
            date_item = QTableWidgetItem(date_str)
            self.actions_table.setItem(row, 2, date_item)
            
            # Status
            status_item = QTableWidgetItem(action['status'].title())
            if action['status'] == 'pending':
                status_item.setForeground(Qt.GlobalColor.blue)
            elif action['status'] == 'executed':
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif action['status'] == 'cancelled':
                status_item.setForeground(Qt.GlobalColor.red)
            self.actions_table.setItem(row, 3, status_item)
            
            # Created Date
            try:
                created_date = datetime.strptime(action['created_date'], '%Y-%m-%d')
                created_str = created_date.strftime('%b %d, %Y')
            except:
                created_str = action['created_date']
            
            created_item = QTableWidgetItem(created_str)
            self.actions_table.setItem(row, 4, created_item)
            
            # Action button(s)
            if action['action_type'] == 'payment_submission' and action['status'] == 'pending' and self.rent_tracker:
                action_container = QFrame()
                action_layout = QHBoxLayout(action_container)
                action_layout.setContentsMargins(0, 0, 0, 0)
                action_layout.setSpacing(4)

                approve_btn = QPushButton('Approve')
                approve_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; border-radius: 4px; padding: 4px 8px;")
                approve_btn.clicked.connect(lambda checked, a_id=action['action_id']: self.approve_payment_submission(a_id))

                deny_btn = QPushButton('Deny')
                deny_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; border-radius: 4px; padding: 4px 8px;")
                deny_btn.clicked.connect(lambda checked, a_id=action['action_id']: self.remove_action(a_id))

                action_layout.addWidget(approve_btn)
                action_layout.addWidget(deny_btn)
                self.actions_table.setCellWidget(row, 5, action_container)
            else:
                remove_btn = QPushButton('Remove')
                remove_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; border-radius: 4px; padding: 4px 10px;")
                remove_btn.clicked.connect(lambda checked, a_id=action['action_id']: self.remove_action(a_id))
                self.actions_table.setCellWidget(row, 5, remove_btn)
            
            # Store action data in the type item (already added to table)
            type_item.setData(Qt.ItemDataRole.UserRole, action)
    
    def remove_action(self, action_id):
        """Remove an action from the queue"""
        logger.debug("ActionQueueDialog", f"Removing action {action_id}")
        action = self.action_queue.get_action(action_id)
        if not action:
            logger.warning("ActionQueueDialog", f"Action not found: {action_id}")
            QMessageBox.warning(self, 'Remove Action', 'Action not found.')
            return
        if action['status'] != 'pending':
            logger.warning("ActionQueueDialog", f"Cannot remove non-pending action {action_id}")
            QMessageBox.warning(self, 'Remove Action', 'Only pending actions can be removed.')
            return
        confirm = QMessageBox.question(self, 'Confirm Remove', f"Are you sure you want to remove this action?\n\n{action['description']}", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.action_queue.cancel_action(action_id, reason='Removed by admin')
            logger.info("ActionQueueDialog", f"Action removed: {action_id}")
            self.load_actions()
            QMessageBox.information(self, 'Action Removed', 'Action has been removed from the queue.')

    def approve_payment_submission(self, action_id):
        """Approve pending payment_submission action from desktop admin UI."""
        if not self.rent_tracker:
            QMessageBox.warning(self, 'Approve Payment', 'Rent tracker is not available.')
            return

        action = self.action_queue.get_action(action_id)
        if not action:
            QMessageBox.warning(self, 'Approve Payment', 'Payment submission action not found.')
            return

        if action.get('action_type') != 'payment_submission' or action.get('status') != 'pending':
            QMessageBox.warning(self, 'Approve Payment', 'Only pending payment submissions can be approved.')
            return

        tenant = self.rent_tracker.tenant_manager.get_tenant(action.get('tenant_id'))
        if not tenant:
            QMessageBox.warning(self, 'Approve Payment', 'Tenant for this payment submission was not found.')
            return

        action_data = action.get('action_data', {})
        amount = float(action_data.get('amount', 0) or 0)
        if amount <= 0:
            QMessageBox.warning(self, 'Approve Payment', 'Invalid payment amount in submission.')
            return

        notes = action_data.get('notes') or None

        success = self.rent_tracker.add_payment(
            tenant.name,
            amount,
            payment_type=action_data.get('payment_type', 'Cash'),
            payment_date=action_data.get('payment_date'),
            payment_month=action_data.get('payment_month') or None,
            notes=notes
        )

        if not success:
            QMessageBox.warning(self, 'Approve Payment', 'Failed to record approved payment.')
            return

        self.action_queue.execute_action(action_id, {
            'approved': True,
            'approved_by': 'desktop_admin',
            'approved_at': datetime.now().isoformat(),
            'tenant_id': action.get('tenant_id'),
            'amount': amount
        })

        logger.info("ActionQueueDialog", f"Approved pending payment submission {action_id}")
        self.load_actions()
        QMessageBox.information(self, 'Approve Payment', 'Payment submission approved and recorded.')
    
    def on_selection_changed(self):
        """Handle selection change to show action details"""
        current_row = self.actions_table.currentRow()
        if current_row >= 0:
            type_item = self.actions_table.item(current_row, 0)
            if type_item:
                action = type_item.data(Qt.ItemDataRole.UserRole)
                if action:
                    logger.debug("ActionQueueDialog", f"Action selected: {action.get('action_id')}")
                    self.show_action_details(action)
    
    def show_action_details(self, action):
        """Show detailed information about an action"""
        details = f"Action ID: {action['action_id']}\\n"
        details += f"Type: {action['action_type']}\\n"
        details += f"Scheduled Date: {action['scheduled_date']}\\n"
        details += f"Status: {action['status']}\\n"
        details += f"Created: {action['created_date']}\\n"
        
        if action.get('executed_date'):
            details += f"Executed: {action['executed_date']}\\n"
        
        details += f"\\nDescription: {action['description']}\\n"
        
        # Show action-specific data
        if action['action_type'] == 'rent_change':
            action_data = action['action_data']
            details += f"\\nRent Change Details:\\n"
            
            # Add tenant information
            tenant_id = action.get('tenant_id', 'Unknown')
            tenant_name = 'Unknown'
            
            # Try to get tenant name using rent_tracker
            if self.rent_tracker:
                try:
                    tenant_obj = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
                    if tenant_obj:
                        tenant_name = tenant_obj.name
                except:
                    pass
            
            details += f"Target Tenant: {tenant_name} (ID: {tenant_id})\\n"
            
            if action_data.get('old_rent') is not None:
                details += f"Old Rent: ${action_data['old_rent']:.2f}\\n"
            details += f"New Rent: ${action_data['new_rent']:.2f}\\n"
            if action_data.get('notes'):
                details += f"Notes: {action_data['notes']}\\n"
        
        elif action['action_type'] == 'notification':
            action_data = action['action_data']
            details += f"\\nNotification Details:\\n"
            details += f"Message: {action_data['message']}\\n"
            details += f"Type: {action_data.get('notification_type', 'general')}\\n"
        elif action['action_type'] == 'payment_submission':
            action_data = action['action_data']
            details += f"\nPayment Submission Details:\n"
            details += f"Amount: ${float(action_data.get('amount', 0) or 0):.2f}\n"
            details += f"Payment Type: {action_data.get('payment_type', 'Online')}\n"
            details += f"Payment Date: {action_data.get('payment_date', 'N/A')}\n"
            details += f"Payment Month: {action_data.get('payment_month', 'N/A') or 'N/A'}\n"
            details += f"Submitted By: {action_data.get('submitted_by', 'Unknown')}\n"
            if action_data.get('notes'):
                details += f"Notes: {action_data.get('notes')}\n"
        
        # Show execution result if available
        if action.get('execution_result'):
            details += f"\\nExecution Result:\\n"
            result = action['execution_result']
            if isinstance(result, dict):
                for key, value in result.items():
                    details += f"{key}: {value}\\n"
            else:
                details += str(result)
        
        self.details_text.setText(details)
    
    def show_cleanup_dialog(self):
        """Show cleanup options dialog"""
        logger.debug("ActionQueueDialog", "Showing cleanup options dialog")
        if not self.action_queue:
            logger.warning("ActionQueueDialog", "No action queue available for cleanup")
            QMessageBox.warning(self, 'Cleanup', 'No action queue available.')
            return
        
        # Create custom dialog with options
        dialog = QDialog(self)
        dialog.setWindowTitle('Cleanup Options')
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Choose Cleanup Option:')
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Option 1: Clean old actions
        old_actions_btn = QPushButton('Clean Old Actions (by date)')
        old_actions_btn.clicked.connect(lambda: self.cleanup_old_actions_dialog(dialog))
        old_actions_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 15px;
                font-size: 14px;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        layout.addWidget(old_actions_btn)
        
        # Option 2: Clean all cancelled
        cancelled_count = self.action_queue.get_cancelled_count()
        cancelled_text = f'Clean All Cancelled Actions ({cancelled_count} found)'
        cancelled_btn = QPushButton(cancelled_text)
        cancelled_btn.clicked.connect(lambda: self.cleanup_all_cancelled_dialog(dialog))
        cancelled_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 15px;
                font-size: 14px;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        cancelled_btn.setEnabled(cancelled_count > 0)
        layout.addWidget(cancelled_btn)
        
        # Cancel button
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(dialog.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        layout.addWidget(cancel_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def cleanup_old_actions_dialog(self, parent_dialog):
        """Handle cleanup of old actions by date"""
        logger.debug("ActionQueueDialog", "Cleanup old actions dialog opened")
        parent_dialog.accept()  # Close the options dialog
        
        # Get cleanup options from user
        days, ok = QInputDialog.getInt(
            self, 
            'Cleanup Old Actions', 
            'Remove executed and cancelled actions older than how many days?',
            value=30,  # default 30 days
            min=1,
            max=365
        )
        
        if not ok:
            logger.debug("ActionQueueDialog", "Cleanup dialog cancelled by user")
            return
        
        logger.debug("ActionQueueDialog", f"Cleanup requested for actions older than {days} days")
        
        # Get statistics first
        try:
            stats = self.action_queue.get_cleanup_statistics(days)
        except Exception as e:
            logger.error("ActionQueueDialog", f"Failed to get cleanup statistics: {str(e)}")
            QMessageBox.critical(self, 'Error', f'Failed to get cleanup statistics: {str(e)}')
            return
        
        if stats['total_candidates'] == 0:
            QMessageBox.information(
                self, 
                'Cleanup Results', 
                f'No executed or cancelled actions older than {days} days found.'
            )
            return
        
        # Show confirmation with statistics
        confirm_msg = (
            f"This will remove {stats['total_candidates']} old actions:\n"
            f"• {stats['executed']} executed actions\n"
            f"• {stats['cancelled']} cancelled actions\n\n"
            f"Actions older than {days} days (before {stats['cutoff_date']}) will be removed.\n\n"
            f"Continue with cleanup?"
        )
        
        confirm = QMessageBox.question(
            self, 
            'Confirm Cleanup', 
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                removed_count = self.action_queue.cleanup_old_actions(days)
                logger.info("ActionQueueDialog", f"Cleanup completed: removed {removed_count} old actions")
                QMessageBox.information(
                    self, 
                    'Cleanup Complete', 
                    f'Successfully removed {removed_count} old actions.'
                )
                # Refresh the table
                self.load_actions()
            except Exception as e:
                logger.error("ActionQueueDialog", f"Cleanup failed: {str(e)}")
                QMessageBox.critical(self, 'Error', f'Cleanup failed: {str(e)}')
    
    def cleanup_all_cancelled_dialog(self, parent_dialog):
        """Handle cleanup of all cancelled actions"""
        logger.debug("ActionQueueDialog", "Cleanup all cancelled actions dialog opened")
        parent_dialog.accept()  # Close the options dialog
        
        cancelled_count = self.action_queue.get_cancelled_count()
        
        if cancelled_count == 0:
            logger.debug("ActionQueueDialog", "No cancelled actions found")
            QMessageBox.information(self, 'Cleanup', 'No cancelled actions found.')
            return
        
        confirm = QMessageBox.question(
            self, 
            'Confirm Cleanup', 
            f'This will remove all {cancelled_count} cancelled actions regardless of date.\n\nContinue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                removed_count = self.action_queue.cleanup_all_cancelled()
                logger.info("ActionQueueDialog", f"Cleanup completed: removed {removed_count} cancelled actions")
                QMessageBox.information(
                    self, 
                    'Cleanup Complete', 
                    f'Successfully removed {removed_count} cancelled actions.'
                )
                # Refresh the table
                self.load_actions()
            except Exception as e:
                logger.error("ActionQueueDialog", f"Cleanup failed: {str(e)}")
                QMessageBox.critical(self, 'Error', f'Cleanup failed: {str(e)}')
