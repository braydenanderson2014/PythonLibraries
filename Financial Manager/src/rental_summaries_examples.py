"""
Example usage of the Rental Summaries system
Demonstrates how to use monthly, yearly, and rental period summaries
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from rental_summaries import RentalSummaries
from rent_tracker import RentTracker
from tenant import TenantManager


def example_monthly_summary():
    """Example: Get and display a monthly summary"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Monthly Summary")
    print("="*70)
    
    # Initialize components
    tenant_manager = TenantManager()
    rent_tracker = RentTracker(tenant_manager=tenant_manager)
    summaries = RentalSummaries(rent_tracker=rent_tracker)
    
    # Get list of tenants
    tenants = tenant_manager.list_tenants()
    if not tenants:
        print("No tenants found in system")
        return
    
    # Use first tenant as example
    tenant = tenants[0]
    tenant_id = tenant.tenant_id
    
    # Generate and print monthly summary for January 2025
    print(f"\nGenerating monthly summary for {tenant.name}...")
    summaries.print_monthly_summary(tenant_id, year=2025, month=1)
    
    # You can also get the summary without printing
    summary = summaries.get_monthly_summary(tenant_id, year=2025, month=1)
    if summary:
        print(f"\nSummary data structure:")
        print(f"  - Expected Rent: ${summary['expected_rent']:.2f}")
        print(f"  - Total Paid: ${summary['total_paid']:.2f}")
        print(f"  - Balance: ${summary['balance']:.2f}")
        print(f"  - Payment Count: {summary['payment_count']}")


def example_yearly_summary():
    """Example: Get and display a yearly summary"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Yearly Summary")
    print("="*70)
    
    # Initialize components
    tenant_manager = TenantManager()
    rent_tracker = RentTracker(tenant_manager=tenant_manager)
    summaries = RentalSummaries(rent_tracker=rent_tracker)
    
    # Get list of tenants
    tenants = tenant_manager.list_tenants()
    if not tenants:
        print("No tenants found in system")
        return
    
    # Use first tenant as example
    tenant = tenants[0]
    tenant_id = tenant.tenant_id
    
    # Generate and print yearly summary for 2025
    print(f"\nGenerating yearly summary for {tenant.name}...")
    summaries.print_yearly_summary(tenant_id, year=2025)
    
    # You can also get the summary for programmatic use
    summary = summaries.get_yearly_summary(tenant_id, year=2025)
    if summary:
        print(f"\nSummary statistics:")
        print(f"  - Total Expected: ${summary['total_expected_rent']:.2f}")
        print(f"  - Total Paid: ${summary['total_paid']:.2f}")
        print(f"  - Total Balance: ${summary['total_balance']:.2f}")
        print(f"  - Payment Rate: {summary['payment_rate']:.1f}%")
        print(f"  - Months Paid: {summary['months_paid']}")
        print(f"  - Months Delinquent: {summary['months_delinquent']}")


def example_rental_period_summary():
    """Example: Get and display a rental period summary"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Rental Period Summary")
    print("="*70)
    
    # Initialize components
    tenant_manager = TenantManager()
    rent_tracker = RentTracker(tenant_manager=tenant_manager)
    summaries = RentalSummaries(rent_tracker=rent_tracker)
    
    # Get list of tenants
    tenants = tenant_manager.list_tenants()
    if not tenants:
        print("No tenants found in system")
        return
    
    # Use first tenant as example
    tenant = tenants[0]
    tenant_id = tenant.tenant_id
    
    # Generate and print complete rental period summary
    print(f"\nGenerating rental period summary for {tenant.name}...")
    summaries.print_rental_period_summary(tenant_id)


def example_export_summaries():
    """Example: Export summaries to JSON and CSV formats"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Export Summaries")
    print("="*70)
    
    # Initialize components
    tenant_manager = TenantManager()
    rent_tracker = RentTracker(tenant_manager=tenant_manager)
    summaries = RentalSummaries(rent_tracker=rent_tracker)
    
    # Get list of tenants
    tenants = tenant_manager.list_tenants()
    if not tenants:
        print("No tenants found in system")
        return
    
    tenant = tenants[0]
    tenant_id = tenant.tenant_id
    
    # Export as JSON
    print(f"\nExporting summaries for {tenant.name}...")
    
    # Monthly summary JSON
    if summaries.export_monthly_summary_json(tenant_id, 2025, 1, 
                                             "monthly_summary.json"):
        print("✓ Monthly summary exported to monthly_summary.json")
    
    # Yearly summary JSON
    if summaries.export_yearly_summary_json(tenant_id, 2025, 
                                            "yearly_summary.json"):
        print("✓ Yearly summary exported to yearly_summary.json")
    
    # Rental period summary JSON
    if summaries.export_rental_period_summary_json(tenant_id, 
                                                    "rental_period_summary.json"):
        print("✓ Rental period summary exported to rental_period_summary.json")
    
    # Export to CSV
    monthly = summaries.get_monthly_summary(tenant_id, 2025, 1)
    if monthly and summaries.export_to_csv(monthly, "monthly_summary.csv", 
                                           summary_type='monthly'):
        print("✓ Monthly summary exported to monthly_summary.csv")
    
    yearly = summaries.get_yearly_summary(tenant_id, 2025)
    if yearly and summaries.export_to_csv(yearly, "yearly_summary.csv", 
                                          summary_type='yearly'):
        print("✓ Yearly summary exported to yearly_summary.csv")
    
    period = summaries.get_rental_period_summary(tenant_id)
    if period and summaries.export_to_csv(period, "rental_period_summary.csv", 
                                          summary_type='period'):
        print("✓ Rental period summary exported to rental_period_summary.csv")


def example_print_all_summaries():
    """Example: Print summaries for all tenants"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Print Summaries for All Tenants")
    print("="*70)
    
    # Initialize components
    tenant_manager = TenantManager()
    rent_tracker = RentTracker(tenant_manager=tenant_manager)
    summaries = RentalSummaries(rent_tracker=rent_tracker)
    
    # Get list of tenants
    tenants = tenant_manager.list_tenants()
    if not tenants:
        print("No tenants found in system")
        return
    
    print(f"\nFound {len(tenants)} tenant(s)\n")
    
    for tenant in tenants:
        tenant_id = tenant.tenant_id
        
        # Print rental period summary for each tenant
        print(f"\n{'='*70}")
        print(f"Generating summary for {tenant.name}")
        print(f"{'='*70}")
        
        summaries.print_rental_period_summary(tenant_id)


def example_custom_date_range():
    """Example: Generate summaries for multiple months"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Generate Summaries for Date Range")
    print("="*70)
    
    # Initialize components
    tenant_manager = TenantManager()
    rent_tracker = RentTracker(tenant_manager=tenant_manager)
    summaries = RentalSummaries(rent_tracker=rent_tracker)
    
    # Get list of tenants
    tenants = tenant_manager.list_tenants()
    if not tenants:
        print("No tenants found in system")
        return
    
    tenant = tenants[0]
    tenant_id = tenant.tenant_id
    
    print(f"\nGenerating summaries for {tenant.name} - Q1 2025\n")
    
    # Generate summaries for Q1 2025
    for month in range(1, 4):
        summary = summaries.get_monthly_summary(tenant_id, 2025, month)
        if summary:
            month_name = summary['month_display']
            print(f"{month_name:<20} Expected: ${summary['expected_rent']:>8.2f}  "
                  f"Paid: ${summary['total_paid']:>8.2f}  "
                  f"Balance: ${summary['balance']:>8.2f}")


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# RENTAL SUMMARIES SYSTEM - USAGE EXAMPLES")
    print("#"*70)
    
    # Run examples
    try:
        example_monthly_summary()
        example_yearly_summary()
        example_rental_period_summary()
        example_export_summaries()
        example_custom_date_range()
        example_print_all_summaries()
        
        print("\n" + "#"*70)
        print("# All examples completed successfully!")
        print("#"*70 + "\n")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
