"""
Rental System Summaries
Provides monthly, yearly, and rent period summaries with display and print functionality
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any
from collections import defaultdict
import json

try:
    from .assets.Logger import Logger
except ImportError:
    from assets.Logger import Logger

logger = Logger()


class RentalSummaries:
    """Generates comprehensive summaries for rental data"""
    
    def __init__(self, rent_tracker=None):
        """
        Initialize rental summaries
        
        Args:
            rent_tracker: RentTracker instance for accessing rental data
        """
        self.rent_tracker = rent_tracker
        logger.debug("RentalSummaries", "Initialized RentalSummaries")
    
    def get_monthly_summary(self, tenant_id: str, year: int, month: int) -> Optional[Dict[str, Any]]:
        """
        Get summary for a specific month
        
        Args:
            tenant_id: Tenant ID
            year: Year (YYYY)
            month: Month (1-12)
            
        Returns:
            Dictionary with monthly summary data
        """
        logger.debug("RentalSummaries", f"Generating monthly summary for {tenant_id}: {year}-{month:02d}")
        
        if not self.rent_tracker:
            logger.warning("RentalSummaries", "No rent_tracker available")
            return None
        
        try:
            tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                logger.warning("RentalSummaries", f"Tenant {tenant_id} not found")
                return None
            
            month_key = f"{year}-{month:02d}"
            
            # Get expected rent - check for overrides first, then base rent
            expected_rent = 0.0
            
            # Check for monthly override first
            if hasattr(tenant, 'monthly_exceptions') and month_key in tenant.monthly_exceptions:
                expected_rent = tenant.monthly_exceptions[month_key]
                logger.debug("RentalSummaries", f"Using monthly override for {month_key}: ${expected_rent}")
            # Check for yearly override
            elif hasattr(tenant, 'monthly_exceptions') and str(year) in tenant.monthly_exceptions:
                expected_rent = tenant.monthly_exceptions[str(year)]
                logger.debug("RentalSummaries", f"Using yearly override for {year}: ${expected_rent}")
            # Use base rent
            else:
                expected_rent = tenant.rent_amount
                logger.debug("RentalSummaries", f"Using base rent for {month_key}: ${expected_rent}")
            
            logger.debug("RentalSummaries", f"Monthly summary for {tenant.name}: {month_key}, expected_rent=${expected_rent}")
            
            # Calculate payments for this month
            total_paid = 0.0
            payments = []
            
            if hasattr(tenant, 'payment_history') and tenant.payment_history:
                logger.debug("RentalSummaries", f"Processing {len(tenant.payment_history)} payments for {tenant.name}")
                for payment in tenant.payment_history:
                    # Handle payment data (skip if not a dict)
                    if not isinstance(payment, dict):
                        logger.debug("RentalSummaries", f"Skipping non-dict payment: {type(payment)}")
                        continue
                    
                    # Check if payment is for this month
                    payment_year = payment.get('year')
                    payment_month = payment.get('month')
                    
                    if payment_year == year and payment_month == month:
                        amount = payment.get('amount', 0)
                        total_paid += amount
                        logger.debug("RentalSummaries", f"Found payment for {year}-{month:02d}: ${amount}")
                        payments.append({
                            'date': payment.get('date', 'Unknown'),
                            'amount': amount,
                            'type': payment.get('type', 'Unknown'),
                            'is_credit_usage': payment.get('is_credit_usage', False)
                        })
            
            # Get monthly status
            monthly_status = 'Unknown'
            if hasattr(tenant, 'monthly_status') and month_key in tenant.monthly_status:
                status_value = tenant.monthly_status[month_key]
                # Handle both string and dict formats
                if isinstance(status_value, dict):
                    monthly_status = status_value.get('status', 'Unknown')
                else:
                    monthly_status = str(status_value) if status_value else 'Unknown'
            
            balance = expected_rent - total_paid
            
            summary = {
                'tenant_id': tenant_id,
                'tenant_name': tenant.name,
                'year': year,
                'month': month,
                'month_display': datetime(year, month, 1).strftime('%B %Y'),
                'expected_rent': expected_rent,
                'total_paid': total_paid,
                'balance': balance,
                'payment_count': len(payments),
                'payments': payments,
                'status': monthly_status,
                'due_date': f"{year}-{month:02d}-{int(tenant.rent_due_date) if tenant.rent_due_date else 1:02d}",
                'is_delinquent': balance > 0 and date(year, month, 1) < date.today()
            }
            
            logger.info("RentalSummaries", f"Monthly summary generated for {tenant.name}: {month_key}")
            return summary
            
        except Exception as e:
            logger.error("RentalSummaries", f"Error generating monthly summary for {tenant_id}: {year}-{month:02d}: {e}")
            import traceback
            logger.error("RentalSummaries", f"Traceback: {traceback.format_exc()}")
            return None
    
    def get_yearly_summary(self, tenant_id: str, year: int) -> Optional[Dict[str, Any]]:
        """
        Get summary for an entire year
        
        Args:
            tenant_id: Tenant ID
            year: Year (YYYY)
            
        Returns:
            Dictionary with yearly summary data
        """
        logger.debug("RentalSummaries", f"Generating yearly summary for {tenant_id}: {year}")
        
        if not self.rent_tracker:
            logger.warning("RentalSummaries", "No rent_tracker available")
            return None
        
        try:
            tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                logger.warning("RentalSummaries", f"Tenant {tenant_id} not found")
                return None
            
            monthly_summaries = []
            total_expected = 0.0
            total_paid = 0.0
            total_balance = 0.0
            delinquent_count = 0
            paid_count = 0
            partial_count = 0
            
            # Get summaries for all 12 months
            for month in range(1, 13):
                monthly = self.get_monthly_summary(tenant_id, year, month)
                if monthly:
                    monthly_summaries.append(monthly)
                    total_expected += monthly['expected_rent']
                    total_paid += monthly['total_paid']
                    total_balance += monthly['balance']
                    
                    # Debug logging for each month
                    month_str = f"{year}-{month:02d}"
                    logger.debug("RentalSummaries", f"Month {month_str}: expected=${monthly['expected_rent']}, paid=${monthly['total_paid']}, balance=${monthly['balance']}, delinquent={monthly['is_delinquent']}, payment_count={monthly['payment_count']}")
                    
                    # Categorize month based on payment status
                    if monthly['is_delinquent']:
                        logger.debug("RentalSummaries", f"  -> Categorized as DELINQUENT")
                        delinquent_count += 1
                    elif monthly['balance'] <= 0:
                        logger.debug("RentalSummaries", f"  -> Categorized as PAID")
                        # Paid in full or overpayment (balance of 0 or negative)
                        paid_count += 1
                    else:
                        # Any month with positive balance that's not delinquent = partial
                        logger.debug("RentalSummaries", f"  -> Categorized as PARTIAL (not delinquent, balance={monthly['balance']} > 0)")
                        partial_count += 1
                else:
                    logger.debug("RentalSummaries", f"Skipping month {year}-{month:02d}: monthly summary returned None")
            
            summary = {
                'tenant_id': tenant_id,
                'tenant_name': tenant.name,
                'year': year,
                'total_expected_rent': total_expected,
                'total_paid': total_paid,
                'total_balance': total_balance,
                'payment_rate': (total_paid / total_expected * 100) if total_expected > 0 else 0,
                'months_paid': paid_count,
                'months_partial': partial_count,
                'months_delinquent': delinquent_count,
                'monthly_details': monthly_summaries
            }
            
            logger.info("RentalSummaries", f"Yearly summary generated for {tenant.name}: {year}")
            return summary
            
        except Exception as e:
            logger.error("RentalSummaries", f"Error generating yearly summary for {tenant_id}: {year}: {e}")
            import traceback
            logger.error("RentalSummaries", f"Traceback: {traceback.format_exc()}")
            return None
    
    def get_rental_period_summary(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive summary for entire rental period
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Dictionary with rental period summary data
        """
        logger.debug("RentalSummaries", f"Generating rental period summary for {tenant_id}")
        
        if not self.rent_tracker:
            logger.warning("RentalSummaries", "No rent_tracker available")
            return None
        
        try:
            tenant = self.rent_tracker.tenant_manager.get_tenant(tenant_id)
            if not tenant:
                logger.warning("RentalSummaries", f"Tenant {tenant_id} not found")
                return None
            
            # Get rental period
            start_date = tenant.rental_period[0] if tenant.rental_period and len(tenant.rental_period) > 0 else None
            end_date = tenant.rental_period[1] if tenant.rental_period and len(tenant.rental_period) > 1 else None
            
            if not start_date or not end_date:
                logger.warning("RentalSummaries", f"Tenant {tenant_id} has incomplete rental period")
                return None
            
            # Parse dates
            if isinstance(start_date, str):
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                except:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S').date()
            
            if isinstance(end_date, str):
                try:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                except:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S').date()
            
            # Collect all yearly summaries for the rental period
            yearly_summaries = []
            current_year = start_date.year
            end_year = end_date.year
            
            # Cap the end date to today - don't include future months
            today = date.today()
            if end_date > today:
                end_date = today
            
            total_expected = 0.0
            total_paid = 0.0
            total_balance = 0.0
            total_months_paid = 0
            total_months_partial = 0
            total_months_delinquent = 0
            
            # Get base rent for comparison
            base_rent = tenant.rent_amount
            logger.debug("RentalSummaries", f"Base rent for comparison: ${base_rent}")
            logger.debug("RentalSummaries", f"Rental period (capped to today): {start_date} to {end_date}")
            
            while current_year <= end_date.year:
                yearly = self.get_yearly_summary(tenant_id, current_year)
                if yearly:
                    yearly_summaries.append(yearly)
                    
                    # Only count months within the actual rental period
                    for monthly in yearly.get('monthly_details', []):
                        month_date = datetime(monthly['year'], monthly['month'], 1).date()
                        
                        logger.debug("RentalSummaries", f"Checking month {monthly['month_display']} ({month_date}) - start={start_date}, end={end_date}")
                        
                        # Skip months before lease start or after today
                        if month_date < start_date or month_date > end_date:
                            logger.debug("RentalSummaries", f"  -> SKIPPED (outside active period)")
                            continue
                        
                        logger.debug("RentalSummaries", f"  -> INCLUDED (balance={monthly['balance']}, base_rent={base_rent}, delinquent={monthly['is_delinquent']})")
                        
                        total_expected += monthly['expected_rent']
                        total_paid += monthly['total_paid']
                        total_balance += monthly['balance']
                        
                        # Categorize independently (a month can be both partial and delinquent)
                        if monthly['balance'] <= 0:
                            logger.debug("RentalSummaries", f"     Categorized as PAID (balance <= 0)")
                            total_months_paid += 1
                        else:
                            # Check if partial (0 < balance < base_rent)
                            if 0 < monthly['balance'] < base_rent:
                                logger.debug("RentalSummaries", f"     Categorized as PARTIAL (0 < {monthly['balance']} < {base_rent})")
                                total_months_partial += 1
                            
                            # Check if delinquent (independent of partial)
                            if monthly['is_delinquent']:
                                logger.debug("RentalSummaries", f"     ALSO Categorized as DELINQUENT")
                                total_months_delinquent += 1
                
                current_year += 1
            
            logger.debug("RentalSummaries", f"Final counts - Paid: {total_months_paid}, Partial: {total_months_partial}, Delinquent: {total_months_delinquent}")

            days_in_period = (end_date - start_date).days
            
            summary = {
                'tenant_id': tenant_id,
                'tenant_name': tenant.name,
                'rental_start_date': start_date.isoformat(),
                'rental_end_date': end_date.isoformat(),
                'rental_period_days': days_in_period,
                'account_status': tenant.account_status,
                'rent_amount': tenant.rent_amount,
                'deposit_amount': tenant.deposit_amount,
                'contact_info': tenant.contact_info,
                'total_expected_rent': total_expected,
                'total_paid': total_paid,
                'total_balance': total_balance,
                'overpayment_credit': tenant.overpayment_credit,
                'service_credit': tenant.service_credit,
                'delinquency_balance': tenant.delinquency_balance,
                'months_paid': total_months_paid,
                'months_partial': total_months_partial,
                'months_delinquent': total_months_delinquent,
                'payment_rate': (total_paid / total_expected * 100) if total_expected > 0 else 0,
                'yearly_summaries': yearly_summaries
            }
            
            logger.info("RentalSummaries", f"Rental period summary generated for {tenant.name}")
            return summary
            
        except Exception as e:
            logger.error("RentalSummaries", f"Error generating rental period summary for {tenant_id}: {e}")
            import traceback
            logger.error("RentalSummaries", f"Traceback: {traceback.format_exc()}")
            return None
    
    def format_monthly_display(self, summary: Dict[str, Any]) -> str:
        """Format monthly summary for display"""
        if not summary:
            return "No summary data available"
        
        display = []
        display.append("=" * 70)
        display.append(f"MONTHLY SUMMARY - {summary['month_display']}")
        display.append("=" * 70)
        display.append(f"Tenant: {summary['tenant_name']} (ID: {summary['tenant_id']})")
        display.append(f"Due Date: {summary['due_date']}")
        display.append("-" * 70)
        display.append(f"Expected Rent:        ${summary['expected_rent']:>10.2f}")
        display.append(f"Total Paid:           ${summary['total_paid']:>10.2f}")
        display.append(f"Balance:              ${summary['balance']:>10.2f}")
        display.append(f"Status:               {summary['status']:<10} {'[DELINQUENT]' if summary['is_delinquent'] else ''}")
        display.append("-" * 70)
        display.append(f"Payment Count:        {summary['payment_count']}")
        
        if summary['payments']:
            display.append("\nPayments:")
            for payment in summary['payments']:
                display.append(f"  • {payment['date']}: ${payment['amount']:>8.2f} ({payment['type']})")
        
        display.append("=" * 70)
        return "\n".join(display)
    
    def format_yearly_display(self, summary: Dict[str, Any]) -> str:
        """Format yearly summary for display"""
        if not summary:
            return "No summary data available"
        
        display = []
        display.append("=" * 70)
        display.append(f"YEARLY SUMMARY - {summary['year']}")
        display.append("=" * 70)
        display.append(f"Tenant: {summary['tenant_name']} (ID: {summary['tenant_id']})")
        display.append("-" * 70)
        display.append(f"Total Expected Rent:  ${summary['total_expected_rent']:>10.2f}")
        display.append(f"Total Paid:           ${summary['total_paid']:>10.2f}")
        display.append(f"Total Balance:        ${summary['total_balance']:>10.2f}")
        display.append(f"Payment Rate:         {summary['payment_rate']:>10.1f}%")
        display.append("-" * 70)
        display.append(f"Months Paid in Full:  {summary['months_paid']:<3} Months")
        display.append(f"Partial Payments:     {summary['months_partial']:<3} Months")
        display.append(f"Delinquent Months:    {summary['months_delinquent']:<3} Months")
        display.append("-" * 70)
        display.append("\nMonthly Breakdown:")
        display.append(f"{'Month':<15} {'Expected':>12} {'Paid':>12} {'Balance':>12} {'Status':<12}")
        display.append("-" * 70)
        
        for monthly in summary['monthly_details']:
            month_name = datetime(monthly['year'], monthly['month'], 1).strftime('%b')
            status = "DELINQUENT" if monthly['is_delinquent'] else "OK"
            display.append(f"{month_name:<15} ${monthly['expected_rent']:>11.2f} ${monthly['total_paid']:>11.2f} ${monthly['balance']:>11.2f} {status:<12}")
        
        display.append("=" * 70)
        return "\n".join(display)
    
    def format_rental_period_display(self, summary: Dict[str, Any]) -> str:
        """Format rental period summary for display"""
        if not summary:
            return "No summary data available"
        
        display = []
        display.append("=" * 80)
        display.append(f"RENTAL PERIOD SUMMARY")
        display.append("=" * 80)
        display.append(f"Tenant: {summary['tenant_name']} (ID: {summary['tenant_id']})")
        display.append(f"Account Status: {summary['account_status'].upper()}")
        display.append("-" * 80)
        display.append(f"Rental Period:        {summary['rental_start_date']} to {summary['rental_end_date']}")
        display.append(f"Period Duration:      {summary['rental_period_days']} days")
        display.append(f"Monthly Rent Amount:  ${summary['rent_amount']:>10.2f}")
        display.append(f"Deposit Amount:       ${summary['deposit_amount']:>10.2f}")
        display.append("-" * 80)
        display.append(f"Total Expected Rent:  ${summary['total_expected_rent']:>10.2f}")
        display.append(f"Total Paid:           ${summary['total_paid']:>10.2f}")
        display.append(f"Total Balance:        ${summary['total_balance']:>10.2f}")
        display.append(f"Overpayment Credit:   ${summary['overpayment_credit']:>10.2f}")
        display.append(f"Service Credit:       ${summary['service_credit']:>10.2f}")
        display.append(f"Delinquency Balance:  ${summary['delinquency_balance']:>10.2f}")
        display.append(f"Payment Rate:         {summary['payment_rate']:>10.1f}%")
        display.append("-" * 80)
        display.append(f"Delinquent Months:    {summary['delinquent_months']:<3} Months")
        
        if summary['contact_info']:
            display.append("-" * 80)
            display.append("Contact Information:")
            for key, value in summary['contact_info'].items():
                display.append(f"  {key}: {value}")
        
        display.append("-" * 80)
        display.append("\nYearly Breakdown:")
        display.append(f"{'Year':<6} {'Expected':>12} {'Paid':>12} {'Balance':>12} {'Rate':>8} {'Delinquent':>6}")
        display.append("-" * 80)
        
        for yearly in summary['yearly_summaries']:
            display.append(f"{yearly['year']:<6} ${yearly['total_expected_rent']:>11.2f} ${yearly['total_paid']:>11.2f} ${yearly['total_balance']:>11.2f} {yearly['payment_rate']:>7.1f}% {yearly['months_delinquent']:>6}")
        
        display.append("=" * 80)
        return "\n".join(display)
    
    def print_monthly_summary(self, tenant_id: str, year: int, month: int) -> bool:
        """
        Generate and print monthly summary
        
        Args:
            tenant_id: Tenant ID
            year: Year
            month: Month
            
        Returns:
            True if successful
        """
        logger.debug("RentalSummaries", f"Printing monthly summary for {tenant_id}: {year}-{month:02d}")
        
        summary = self.get_monthly_summary(tenant_id, year, month)
        if summary:
            formatted = self.format_monthly_display(summary)
            print(formatted)
            logger.info("RentalSummaries", "Monthly summary printed successfully")
            return True
        
        logger.warning("RentalSummaries", "Failed to generate monthly summary for printing")
        return False
    
    def print_yearly_summary(self, tenant_id: str, year: int) -> bool:
        """
        Generate and print yearly summary
        
        Args:
            tenant_id: Tenant ID
            year: Year
            
        Returns:
            True if successful
        """
        logger.debug("RentalSummaries", f"Printing yearly summary for {tenant_id}: {year}")
        
        summary = self.get_yearly_summary(tenant_id, year)
        if summary:
            formatted = self.format_yearly_display(summary)
            print(formatted)
            logger.info("RentalSummaries", "Yearly summary printed successfully")
            return True
        
        logger.warning("RentalSummaries", "Failed to generate yearly summary for printing")
        return False
    
    def print_rental_period_summary(self, tenant_id: str) -> bool:
        """
        Generate and print rental period summary
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            True if successful
        """
        logger.debug("RentalSummaries", f"Printing rental period summary for {tenant_id}")
        
        summary = self.get_rental_period_summary(tenant_id)
        if summary:
            formatted = self.format_rental_period_display(summary)
            print(formatted)
            logger.info("RentalSummaries", "Rental period summary printed successfully")
            return True
        
        logger.warning("RentalSummaries", "Failed to generate rental period summary for printing")
        return False
    
    def export_monthly_summary_json(self, tenant_id: str, year: int, month: int, filepath: str) -> bool:
        """Export monthly summary as JSON"""
        try:
            summary = self.get_monthly_summary(tenant_id, year, month)
            if summary:
                with open(filepath, 'w') as f:
                    json.dump(summary, f, indent=2, default=str)
                logger.info("RentalSummaries", f"Monthly summary exported to {filepath}")
                return True
        except Exception as e:
            logger.error("RentalSummaries", f"Failed to export monthly summary: {e}")
        return False
    
    def export_yearly_summary_json(self, tenant_id: str, year: int, filepath: str) -> bool:
        """Export yearly summary as JSON"""
        try:
            summary = self.get_yearly_summary(tenant_id, year)
            if summary:
                with open(filepath, 'w') as f:
                    json.dump(summary, f, indent=2, default=str)
                logger.info("RentalSummaries", f"Yearly summary exported to {filepath}")
                return True
        except Exception as e:
            logger.error("RentalSummaries", f"Failed to export yearly summary: {e}")
        return False
    
    def export_rental_period_summary_json(self, tenant_id: str, filepath: str) -> bool:
        """Export rental period summary as JSON"""
        try:
            summary = self.get_rental_period_summary(tenant_id)
            if summary:
                with open(filepath, 'w') as f:
                    json.dump(summary, f, indent=2, default=str)
                logger.info("RentalSummaries", f"Rental period summary exported to {filepath}")
                return True
        except Exception as e:
            logger.error("RentalSummaries", f"Failed to export rental period summary: {e}")
        return False
    
    def export_to_csv(self, summary: Dict[str, Any], filepath: str, summary_type: str = 'yearly') -> bool:
        """
        Export summary to CSV format
        
        Args:
            summary: Summary dictionary
            filepath: Path to save CSV
            summary_type: Type of summary ('monthly', 'yearly', 'period')
            
        Returns:
            True if successful
        """
        try:
            import csv
            from datetime import datetime
            
            if summary_type == 'monthly':
                rows = [
                    ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                    [],
                    ['Metric', 'Value'],
                    ['Tenant', summary['tenant_name']],
                    ['Month', summary['month_display']],
                    ['Expected Rent', f"${summary['expected_rent']:.2f}"],
                    ['Total Paid', f"${summary['total_paid']:.2f}"],
                    ['Balance', f"${summary['balance']:.2f}"],
                    ['Status', summary['status']],
                    ['Delinquent', 'Yes' if summary['is_delinquent'] else 'No'],
                ]
                
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
            
            elif summary_type == 'yearly':
                rows = [
                    ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                    [],
                    ['Month', 'Expected', 'Paid', 'Balance', 'Status']
                ]
                
                for monthly in summary['monthly_details']:
                    month_name = datetime(monthly['year'], monthly['month'], 1).strftime('%B')
                    status = "Delinquent" if monthly['is_delinquent'] else "OK"
                    rows.append([
                        month_name,
                        f"${monthly['expected_rent']:.2f}",
                        f"${monthly['total_paid']:.2f}",
                        f"${monthly['balance']:.2f}",
                        status
                    ])
                
                rows.extend([
                    [],
                    ['Total', f"${summary['total_expected_rent']:.2f}", 
                     f"${summary['total_paid']:.2f}", 
                     f"${summary['total_balance']:.2f}", '']
                ])
                
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
            
            elif summary_type == 'period':
                rows = [
                    ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                    [],
                    ['Year', 'Expected', 'Paid', 'Balance', 'Payment Rate']
                ]
                
                for yearly in summary['yearly_summaries']:
                    rows.append([
                        yearly['year'],
                        f"${yearly['total_expected_rent']:.2f}",
                        f"${yearly['total_paid']:.2f}",
                        f"${yearly['total_balance']:.2f}",
                        f"{yearly['payment_rate']:.1f}%"
                    ])
                
                rows.extend([
                    [],
                    ['Total', f"${summary['total_expected_rent']:.2f}",
                     f"${summary['total_paid']:.2f}",
                     f"${summary['total_balance']:.2f}",
                     f"{summary['payment_rate']:.1f}%"]
                ])
                
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
            
            logger.info("RentalSummaries", f"Summary exported to CSV: {filepath}")
            return True
            
        except Exception as e:
            logger.error("RentalSummaries", f"Failed to export summary to CSV: {e}")
            return False
