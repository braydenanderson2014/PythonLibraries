#!/usr/bin/env python3
"""
Debug script to test tenant recalculation in isolation
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.rent_tracker import RentTracker
from src.tenant import TenantManager

def main():
    print("=== Tenant Recalculation Debug ===")
    
    try:
        # Initialize rent tracker
        rent_tracker = RentTracker()
        
        # Get the problem tenant
        tenant = rent_tracker.tenant_manager.get_tenant("NPd0u6vPVi")
        if not tenant:
            print("Tenant NPd0u6vPVi not found!")
            return
            
        print(f"Tenant: {tenant.name}")
        print(f"Rental period: {tenant.rental_period}")
        print(f"Current months_to_charge: {tenant.months_to_charge}")
        print(f"Current delinquent_months: {tenant.delinquent_months}")
        print(f"Current delinquency_balance: {tenant.delinquency_balance}")
        
        print("\n--- Testing ensure_months_to_charge ---")
        rent_tracker.ensure_months_to_charge(tenant)
        print(f"After ensure_months_to_charge: {tenant.months_to_charge}")
        
        print("\n--- Testing check_and_update_delinquency ---")
        rent_tracker.check_and_update_delinquency(target_tenant_id="NPd0u6vPVi")
        
        print(f"After recalculation:")
        print(f"  months_to_charge: {tenant.months_to_charge}")
        print(f"  delinquent_months: {tenant.delinquent_months}")
        print(f"  delinquency_balance: {tenant.delinquency_balance}")
        print(f"  monthly_status keys: {list(tenant.monthly_status.keys()) if hasattr(tenant, 'monthly_status') else 'None'}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()