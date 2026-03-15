"""
Database utilities and helpers for the Financial Manager
Provides convenient functions for database operations and sync management
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from .database import DatabaseManager
except ImportError:
    from database import DatabaseManager
from assets.Logger import Logger
logger = Logger()

class DatabaseValidator:
    """Validates and reports on database/JSON mismatches"""
    
    @staticmethod
    def format_mismatch_report(mismatches: Dict[str, Any]) -> str:
        """Format mismatch data for display"""
        logger.debug("DatabaseValidator", f"Formatting mismatch report")
        
        # Handle the new mismatch summary format
        if not mismatches:
            logger.info("DatabaseValidator", "No mismatches found")
            return "No mismatches found."
        
        # Check if this is the new format (tenant_mismatches, payment_mismatches keys)
        if 'tenant_mismatches' in mismatches or 'payment_mismatches' in mismatches:
            report = "=== DATABASE MISMATCH REPORT ===\n"
            tenant_count = mismatches.get('tenant_mismatches', 0)
            payment_count = mismatches.get('payment_mismatches', 0)
            
            if tenant_count == 0 and payment_count == 0:
                return "✓ No mismatches found - Database is in sync!"
            
            report += f"\nTenant Mismatches: {tenant_count}\n"
            report += f"Payment Mismatches: {payment_count}\n"
            
            # Add details if available
            details = mismatches.get('details', [])
            if details:
                report += "\n--- Details ---\n"
                for detail in details:
                    report += f"  • {detail}\n"
                    logger.debug("DatabaseValidator", f"Mismatch detail: {detail}")
            
            logger.info("DatabaseValidator", f"Mismatch report: {tenant_count} tenant, {payment_count} payment")
            return report
        
        # Fall back to old format (entity_type: {field: count})
        report = "=== DATABASE MISMATCH REPORT ===\n"
        
        for entity_type, fields in mismatches.items():
            if isinstance(fields, dict):
                report += f"\n{entity_type.upper()}:\n"
                for field, count in fields.items():
                    report += f"  - {field}: {count} mismatch(es)\n"
                    logger.debug("DatabaseValidator", f"Mismatch in {entity_type}.{field}: {count} issues")
        
        logger.info("DatabaseValidator", "Mismatch report formatted successfully")
        return report
    
    @staticmethod
    def format_sync_logs(logs: List[Dict]) -> str:
        """Format sync logs for display"""
        logger.debug("DatabaseValidator", f"Formatting {len(logs)} sync logs")
        if not logs:
            logger.info("DatabaseValidator", "No sync logs available")
            return "No sync logs available."
        
        report = "=== RECENT SYNC LOGS ===\n"
        
        for log in logs:
            report += f"\n[{log['timestamp']}] {log['entity_type'].upper()}: {log['entity_id']}\n"
            report += f"  Mismatch Fields: {log['mismatch_type']}\n"
            logger.debug("DatabaseValidator", f"Processing log for {log['entity_type']} {log['entity_id']}")
            
            if log['notes']:
                try:
                    mismatches = json.loads(log['notes'])
                    for mismatch in mismatches:
                        field = mismatch.get('field', 'unknown')
                        json_val = mismatch.get('json_value', 'N/A')
                        db_val = mismatch.get('db_value', 'N/A')
                        report += f"    {field}: JSON={json_val} vs DB={db_val}\n"
                        logger.debug("DatabaseValidator", f"Mismatch detail - {field}: JSON={json_val} vs DB={db_val}")
                except Exception as e:
                    logger.warning("DatabaseValidator", f"Failed to parse mismatch notes: {str(e)}")
                    report += f"  Details: {log['notes']}\n"
        
        logger.info("DatabaseValidator", "Sync logs formatted successfully")
        return report


class DatabaseUI:
    """Provides UI components and dialogs for database management"""
    
    @staticmethod
    def create_sync_status_dialog(rent_tracker):
        """Create a dialog showing database sync status"""
        logger.debug("DatabaseUI", "Creating sync status dialog")
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QMessageBox
        from PyQt6.QtCore import Qt
        
        dialog = QDialog()
        dialog.setWindowTitle('Database Sync Status')
        dialog.setMinimumSize(700, 500)
        logger.debug("DatabaseUI", "Dialog initialized")
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('Database Synchronization Status')
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #0056b3;")
        layout.addWidget(title)
        
        # Status info
        try:
            status = rent_tracker.get_database_sync_status()
            info_text = f"Database: {status['database_path']}\n"
            info_text += f"Last Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            layout.addWidget(QLabel(info_text))
            logger.info("DatabaseUI", f"Loaded status from {status['database_path']}")
        except Exception as e:
            logger.error("DatabaseUI", f"Error reading status: {str(e)}")
            layout.addWidget(QLabel(f"Error reading status: {e}"))
        
        # Mismatch summary
        layout.addWidget(QLabel('Mismatch Summary:'))
        summary_text = QTextEdit()
        summary_text.setReadOnly(True)
        
        try:
            status = rent_tracker.get_database_sync_status()
            report = DatabaseValidator.format_mismatch_report(status['mismatch_summary'])
            summary_text.setText(report)
            logger.debug("DatabaseUI", "Mismatch summary populated")
        except Exception as e:
            logger.error("DatabaseUI", f"Error formatting mismatch summary: {str(e)}")
            summary_text.setText(f"Error: {e}")
        
        layout.addWidget(summary_text)
        
        # Recent logs
        layout.addWidget(QLabel('Recent Sync Logs:'))
        logs_text = QTextEdit()
        logs_text.setReadOnly(True)
        
        try:
            status = rent_tracker.get_database_sync_status()
            logs_report = DatabaseValidator.format_sync_logs(status['recent_logs'])
            logs_text.setText(logs_report)
            logger.debug("DatabaseUI", "Recent sync logs populated")
        except Exception as e:
            logger.error("DatabaseUI", f"Error formatting sync logs: {str(e)}")
            logs_text.setText(f"Error: {e}")
        
        layout.addWidget(logs_text)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        sync_btn = QPushButton('Sync Now')
        view_btn = QPushButton('View Database')
        wipe_btn = QPushButton('Wipe Database')
        wipe_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        close_btn = QPushButton('Close')
        
        def perform_sync():
            try:
                logger.info("DatabaseUI", "Starting database sync")
                result = rent_tracker.sync_all_tenants_to_database()
                msg = f"✓ Sync Complete!\n\n"
                msg += f"Tenants Synced: {result['synced']}\n"
                msg += f"Payments Synced: {result.get('payments_synced', 0)}\n"
                msg += f"Failed: {result['failed']}\n"
                msg += f"Mismatches Found: {len(result['mismatches'])}"
                logger.info("DatabaseUI", f"Sync complete - Synced: {result['synced']}, Payments: {result.get('payments_synced', 0)}, Failed: {result['failed']}, Mismatches: {len(result['mismatches'])}")
                
                # Update the summary text with results
                sync_results = f"=== LAST SYNC RESULTS ===\n"
                sync_results += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                sync_results += f"Tenants Synced: {result['synced']}\n"
                sync_results += f"Payments Synced: {result.get('payments_synced', 0)}\n"
                sync_results += f"Failed: {result['failed']}\n"
                sync_results += f"Mismatches Found: {len(result['mismatches'])}\n"
                
                if result['mismatches']:
                    sync_results += "\n--- Mismatches ---\n"
                    for mismatch in result['mismatches']:
                        if isinstance(mismatch, dict):
                            tenant_id = mismatch.get('tenant_id', 'Unknown')
                            name = mismatch.get('name', 'Unknown')
                            sync_results += f"\n{tenant_id} ({name}):\n"
                            if 'mismatches' in mismatch:
                                mismatches_list = mismatch['mismatches']
                                if isinstance(mismatches_list, list):
                                    for m in mismatches_list:
                                        sync_results += f"  {m}\n"
                                else:
                                    sync_results += f"  {mismatches_list}\n"
                
                summary_text.setText(sync_results)
                
                QMessageBox.information(dialog, 'Sync Complete', msg)
            except Exception as e:
                logger.error("DatabaseUI", f"Sync failed: {str(e)}")
                QMessageBox.critical(dialog, 'Sync Error', f'Failed to sync: {e}')
        
        def view_database_contents():
            """View all tenants currently in the database"""
            try:
                logger.info("DatabaseUI", "Loading database contents")
                db_manager = DatabaseManager()
                tenants = db_manager.get_all_tenants()
                
                db_view = f"=== DATABASE CONTENTS ({len(tenants)} tenants) ===\n\n"
                
                for tenant in tenants:
                    db_view += f"Tenant ID: {tenant.get('tenant_id', 'N/A')}\n"
                    db_view += f"Name: {tenant.get('name', 'N/A')}\n"
                    db_view += f"Email: {tenant.get('email', 'N/A')}\n"
                    db_view += f"Phone: {tenant.get('phone', 'N/A')}\n"
                    db_view += f"Unit: {tenant.get('unit_number', 'N/A')}\n"
                    db_view += f"Move In: {tenant.get('move_in_date', 'N/A')}\n"
                    db_view += f"Rent Amount: ${tenant.get('rent_amount', 0)}\n"
                    db_view += f"Created: {tenant.get('created_at', 'N/A')}\n"
                    db_view += f"Updated: {tenant.get('updated_at', 'N/A')}\n"
                    db_view += "-" * 50 + "\n\n"
                
                summary_text.setText(db_view)
                QMessageBox.information(dialog, 'Database Contents', f'Loaded {len(tenants)} tenants from database')
            except Exception as e:
                logger.error("DatabaseUI", f"Failed to load database contents: {str(e)}")
                QMessageBox.critical(dialog, 'Error', f'Failed to load database: {e}')
        
        def wipe_database():
            """Wipe all tenants and payments from the database"""
            try:
                logger.info("DatabaseUI", "Wipe database requested")
                # Confirm with user
                confirm = QMessageBox.warning(
                    dialog,
                    'Confirm Wipe Database',
                    'This will DELETE ALL tenants and payments from the database!\n\n'
                    'This action cannot be undone.\n'
                    'Click OK to proceed or Cancel to abort.',
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
                )
                
                if confirm != QMessageBox.StandardButton.Ok:
                    logger.info("DatabaseUI", "Wipe database cancelled by user")
                    return
                
                # Wipe the database
                db_manager = DatabaseManager()
                
                # Get all tenants and delete them
                tenants = db_manager.get_all_tenants()
                deleted_count = 0
                
                for tenant in tenants:
                    try:
                        db_manager.delete_tenant(tenant.get('tenant_id'))
                        deleted_count += 1
                    except Exception as e:
                        logger.warning("DatabaseUI", f"Failed to delete tenant {tenant.get('tenant_id')}: {e}")
                
                # Also clear the sync log to remove stale mismatch records
                try:
                    db_manager.execute_query('DELETE FROM sync_log')
                    db_manager.commit()
                    logger.info("DatabaseUI", "Cleared sync_log table")
                except Exception as e:
                    logger.warning("DatabaseUI", f"Failed to clear sync_log: {e}")
                
                logger.info("DatabaseUI", f"Database wiped - deleted {deleted_count} tenants and cleared sync logs")
                
                # Update display
                summary_text.setText("=== DATABASE WIPED ===\n\n"
                                    f"Deleted {deleted_count} tenants\n"
                                    "Cleared sync logs\n"
                                    "Database is now empty and ready to resync.\n\n"
                                    "Click 'Sync Now' to sync from JSON file.")
                
                QMessageBox.information(dialog, 'Database Wiped', 
                                       f'Successfully deleted {deleted_count} tenants from database.\n\n'
                                       'You can now click "Sync Now" to resync from the JSON file.')
            except Exception as e:
                logger.error("DatabaseUI", f"Failed to wipe database: {str(e)}")
                QMessageBox.critical(dialog, 'Wipe Error', f'Failed to wipe database: {e}')
        
        sync_btn.clicked.connect(perform_sync)
        view_btn.clicked.connect(view_database_contents)
        wipe_btn.clicked.connect(wipe_database)
        close_btn.clicked.connect(dialog.accept)
        logger.debug("DatabaseUI", "Sync, view, wipe, and close buttons connected")
        
        btn_layout.addWidget(sync_btn)
        btn_layout.addWidget(view_btn)
        btn_layout.addWidget(wipe_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        logger.debug("DatabaseUI", "Sync status dialog created successfully")
        return dialog
