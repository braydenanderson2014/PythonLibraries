"""
Rental Summaries UI Integration
Example UI components for displaying and printing rental summaries
"""

# This file demonstrates how to integrate RentalSummaries into a PyQt6 UI
# Suitable for integration with main_window.py or other UI components

class RentalSummariesWidget:
    """
    Example UI widget for displaying rental summaries
    Can be integrated into PyQt6 applications
    """
    
    def __init__(self, parent=None):
        """Initialize the widget"""
        self.parent = parent
        self.summaries = None
        self.current_tenant_id = None
        # Note: Actual PyQt imports would go here
    
    def setup_summaries(self, rent_tracker):
        """Setup summaries system"""
        from rental_summaries import RentalSummaries
        self.summaries = RentalSummaries(rent_tracker=rent_tracker)
    
    # Menu Actions
    def action_show_monthly_summary(self, tenant_id, year, month):
        """Show monthly summary in dialog/window"""
        if not self.summaries:
            return False
        
        summary = self.summaries.get_monthly_summary(tenant_id, year, month)
        if summary:
            display_text = self.summaries.format_monthly_display(summary)
            self.show_text_dialog("Monthly Summary", display_text)
            return True
        return False
    
    def action_show_yearly_summary(self, tenant_id, year):
        """Show yearly summary in dialog/window"""
        if not self.summaries:
            return False
        
        summary = self.summaries.get_yearly_summary(tenant_id, year)
        if summary:
            display_text = self.summaries.format_yearly_display(summary)
            self.show_text_dialog("Yearly Summary", display_text)
            return True
        return False
    
    def action_show_rental_period_summary(self, tenant_id):
        """Show complete rental period summary"""
        if not self.summaries:
            return False
        
        summary = self.summaries.get_rental_period_summary(tenant_id)
        if summary:
            display_text = self.summaries.format_rental_period_display(summary)
            self.show_text_dialog("Rental Period Summary", display_text)
            return True
        return False
    
    # Print Actions
    def action_print_monthly_summary(self, tenant_id, year, month):
        """Print monthly summary to console/file"""
        if not self.summaries:
            return False
        
        return self.summaries.print_monthly_summary(tenant_id, year, month)
    
    def action_print_yearly_summary(self, tenant_id, year):
        """Print yearly summary"""
        if not self.summaries:
            return False
        
        return self.summaries.print_yearly_summary(tenant_id, year)
    
    def action_print_rental_period_summary(self, tenant_id):
        """Print complete rental period summary"""
        if not self.summaries:
            return False
        
        return self.summaries.print_rental_period_summary(tenant_id)
    
    # Export Actions
    def action_export_monthly_as_json(self, tenant_id, year, month, filepath):
        """Export monthly summary to JSON"""
        if not self.summaries:
            return False
        
        return self.summaries.export_monthly_summary_json(
            tenant_id, year, month, filepath
        )
    
    def action_export_yearly_as_json(self, tenant_id, year, filepath):
        """Export yearly summary to JSON"""
        if not self.summaries:
            return False
        
        return self.summaries.export_yearly_summary_json(
            tenant_id, year, filepath
        )
    
    def action_export_period_as_json(self, tenant_id, filepath):
        """Export rental period summary to JSON"""
        if not self.summaries:
            return False
        
        return self.summaries.export_rental_period_summary_json(
            tenant_id, filepath
        )
    
    def action_export_as_csv(self, tenant_id, year, summary_type, filepath):
        """
        Export summary to CSV
        
        Args:
            tenant_id: Tenant ID
            year: Year for monthly/yearly
            summary_type: 'monthly', 'yearly', or 'period'
            filepath: Path to save CSV
        """
        if not self.summaries:
            return False
        
        if summary_type == 'monthly':
            # Assume month 1 if not specified, or pass month separately
            summary = self.summaries.get_monthly_summary(tenant_id, year, 1)
        elif summary_type == 'yearly':
            summary = self.summaries.get_yearly_summary(tenant_id, year)
        elif summary_type == 'period':
            summary = self.summaries.get_rental_period_summary(tenant_id)
        else:
            return False
        
        if summary:
            return self.summaries.export_to_csv(
                summary, filepath, summary_type=summary_type
            )
        return False
    
    # Display Helpers
    def show_text_dialog(self, title, text):
        """Show text in a dialog window"""
        # This would be implemented with PyQt6 in actual usage
        print(f"\n{title}\n{text}")
    
    def get_summary_as_dict(self, tenant_id, summary_type='period', year=None, month=None):
        """
        Get summary as dictionary for programmatic use
        
        Args:
            tenant_id: Tenant ID
            summary_type: 'monthly', 'yearly', or 'period'
            year: Year (required for monthly/yearly)
            month: Month (required for monthly)
            
        Returns:
            Summary dictionary or None
        """
        if not self.summaries:
            return None
        
        if summary_type == 'monthly' and year and month:
            return self.summaries.get_monthly_summary(tenant_id, year, month)
        elif summary_type == 'yearly' and year:
            return self.summaries.get_yearly_summary(tenant_id, year)
        elif summary_type == 'period':
            return self.summaries.get_rental_period_summary(tenant_id)
        
        return None


# ============================================================================
# Integration Examples for Specific UI Frameworks
# ============================================================================

class PyQt6SummariesDialog:
    """
    Example PyQt6 dialog for displaying summaries
    Would inherit from QDialog in actual implementation
    """
    
    def __init__(self, summaries_widget):
        """Initialize dialog"""
        self.widget = summaries_widget
        # PyQt6 init code would go here
    
    def show_monthly_summary_dialog(self, tenant_id, year, month):
        """Show monthly summary in scrollable dialog"""
        summary = self.widget.get_summary_as_dict(
            tenant_id, 'monthly', year, month
        )
        
        if summary:
            text = self.widget.summaries.format_monthly_display(summary)
            # Show in QTextEdit within QDialog
            # Would use PyQt6 in actual implementation
            print(text)
    
    def show_yearly_summary_dialog(self, tenant_id, year):
        """Show yearly summary with monthly breakdown"""
        summary = self.widget.get_summary_as_dict(
            tenant_id, 'yearly', year
        )
        
        if summary:
            text = self.widget.summaries.format_yearly_display(summary)
            # Show in QTextEdit within QDialog
            print(text)
    
    def show_export_dialog(self, tenant_id):
        """Show export options dialog"""
        # Would present user with:
        # - Export format options (JSON, CSV)
        # - Summary type selection (monthly, yearly, period)
        # - Date range selection
        # - Filepath input
        pass


# ============================================================================
# Integration with Main Window
# ============================================================================

class MainWindowIntegration:
    """
    Example of how to integrate summaries into main_window.py
    """
    
    def __init__(self, main_window):
        """Initialize integration"""
        self.main_window = main_window
        self.summaries_widget = RentalSummariesWidget(parent=main_window)
    
    def setup_summaries_menu(self):
        """
        Add summaries menu to main window
        
        Would add menu items like:
        - View → Rental Summaries → Monthly...
        - View → Rental Summaries → Yearly...
        - View → Rental Summaries → Rental Period...
        - File → Export → Rental Summary as JSON...
        - File → Export → Rental Summary as CSV...
        - File → Print → Rental Summary...
        """
        pass
    
    def setup_summaries_toolbar(self):
        """Add toolbar buttons for quick access to summaries"""
        # Add buttons for:
        # - Monthly Summary
        # - Yearly Summary
        # - Rental Period Summary
        pass
    
    def open_monthly_summary(self):
        """Open dialog to select tenant and month for monthly summary"""
        # Prompt user to select:
        # - Tenant (from dropdown)
        # - Year (from calendar)
        # - Month (from calendar)
        # Then call: self.summaries_widget.action_show_monthly_summary()
        pass
    
    def open_yearly_summary(self):
        """Open dialog to select tenant and year for yearly summary"""
        # Similar to monthly but only select year
        pass
    
    def open_rental_period_summary(self):
        """Open dialog to select tenant for rental period summary"""
        # Just select tenant, rest is automatic
        pass


# ============================================================================
# Report Generation Automation
# ============================================================================

class SummaryReportGenerator:
    """
    Automated report generation for rental summaries
    Can run on schedule or on-demand
    """
    
    def __init__(self, summaries_widget):
        """Initialize generator"""
        self.widget = summaries_widget
    
    def generate_monthly_reports_for_all_tenants(self, year, month, output_dir):
        """Generate monthly reports for all tenants"""
        from tenant import TenantManager
        
        tenant_manager = TenantManager()
        tenants = tenant_manager.list_tenants()
        
        results = []
        for tenant in tenants:
            # JSON
            json_file = f"{output_dir}/monthly_{tenant.tenant_id}_{year}_{month:02d}.json"
            json_success = self.widget.action_export_monthly_as_json(
                tenant.tenant_id, year, month, json_file
            )
            
            # CSV
            csv_file = f"{output_dir}/monthly_{tenant.tenant_id}_{year}_{month:02d}.csv"
            summary = self.widget.get_summary_as_dict(
                tenant.tenant_id, 'monthly', year, month
            )
            csv_success = (self.widget.summaries.export_to_csv(
                summary, csv_file, 'monthly'
            ) if summary else False)
            
            results.append({
                'tenant': tenant.name,
                'json': json_success,
                'csv': csv_success
            })
        
        return results
    
    def generate_yearly_reports_for_all_tenants(self, year, output_dir):
        """Generate yearly reports for all tenants"""
        from tenant import TenantManager
        
        tenant_manager = TenantManager()
        tenants = tenant_manager.list_tenants()
        
        results = []
        for tenant in tenants:
            # JSON
            json_file = f"{output_dir}/yearly_{tenant.tenant_id}_{year}.json"
            json_success = self.widget.action_export_yearly_as_json(
                tenant.tenant_id, year, json_file
            )
            
            # CSV
            csv_file = f"{output_dir}/yearly_{tenant.tenant_id}_{year}.csv"
            summary = self.widget.get_summary_as_dict(
                tenant.tenant_id, 'yearly', year
            )
            csv_success = (self.widget.summaries.export_to_csv(
                summary, csv_file, 'yearly'
            ) if summary else False)
            
            results.append({
                'tenant': tenant.name,
                'json': json_success,
                'csv': csv_success
            })
        
        return results
    
    def generate_rental_period_reports_for_all_tenants(self, output_dir):
        """Generate complete rental period reports for all tenants"""
        from tenant import TenantManager
        
        tenant_manager = TenantManager()
        tenants = tenant_manager.list_tenants()
        
        results = []
        for tenant in tenants:
            # JSON
            json_file = f"{output_dir}/rental_period_{tenant.tenant_id}.json"
            json_success = self.widget.action_export_period_as_json(
                tenant.tenant_id, json_file
            )
            
            # CSV
            csv_file = f"{output_dir}/rental_period_{tenant.tenant_id}.csv"
            summary = self.widget.get_summary_as_dict(
                tenant.tenant_id, 'period'
            )
            csv_success = (self.widget.summaries.export_to_csv(
                summary, csv_file, 'period'
            ) if summary else False)
            
            results.append({
                'tenant': tenant.name,
                'json': json_success,
                'csv': csv_success
            })
        
        return results


# ============================================================================
# CLI Integration for Command-Line Usage
# ============================================================================

class SummariesCLI:
    """
    Command-line interface for rental summaries
    Can be used for scripting and automation
    """
    
    def __init__(self, summaries_widget):
        """Initialize CLI"""
        self.widget = summaries_widget
    
    def cmd_monthly(self, tenant_id, year, month, output_format='console'):
        """
        Command: monthly [tenant_id] [year] [month] [--json|--csv|--console]
        """
        if output_format == 'json':
            filepath = f"monthly_{tenant_id}_{year}_{month:02d}.json"
            return self.widget.action_export_monthly_as_json(
                tenant_id, year, month, filepath
            )
        elif output_format == 'csv':
            filepath = f"monthly_{tenant_id}_{year}_{month:02d}.csv"
            return self.widget.action_export_as_csv(
                tenant_id, year, 'monthly', filepath
            )
        else:  # console
            return self.widget.action_print_monthly_summary(
                tenant_id, year, month
            )
    
    def cmd_yearly(self, tenant_id, year, output_format='console'):
        """
        Command: yearly [tenant_id] [year] [--json|--csv|--console]
        """
        if output_format == 'json':
            filepath = f"yearly_{tenant_id}_{year}.json"
            return self.widget.action_export_yearly_as_json(
                tenant_id, year, filepath
            )
        elif output_format == 'csv':
            filepath = f"yearly_{tenant_id}_{year}.csv"
            return self.widget.action_export_as_csv(
                tenant_id, year, 'yearly', filepath
            )
        else:  # console
            return self.widget.action_print_yearly_summary(tenant_id, year)
    
    def cmd_period(self, tenant_id, output_format='console'):
        """
        Command: period [tenant_id] [--json|--csv|--console]
        """
        if output_format == 'json':
            filepath = f"rental_period_{tenant_id}.json"
            return self.widget.action_export_period_as_json(
                tenant_id, filepath
            )
        elif output_format == 'csv':
            filepath = f"rental_period_{tenant_id}.csv"
            return self.widget.action_export_as_csv(
                tenant_id, 0, 'period', filepath
            )
        else:  # console
            return self.widget.action_print_rental_period_summary(tenant_id)
