#!/usr/bin/env python3
"""Debug script to check tenant data loading."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_tenant_loading():
    print("=== Testing Tenant Data Loading ===")
    
    try:
        from src.tenant import TenantManager
        
        # Load tenant manager
        tm = TenantManager()
        tm.load()
        
        print(f"Loaded {len(tm.tenants)} tenants")
        
        # Find Testing Program tenant
        testing_tenant = None
        for tid, tenant in tm.tenants.items():
            if tenant.name == "Testing Program":
                testing_tenant = tenant
                break
        
        if testing_tenant:
            print(f"\nFound Testing Program tenant:")
            print(f"  ID: {testing_tenant.tenant_id}")
            print(f"  Name: {testing_tenant.name}")
            print(f"  Has deposit_amount attr: {hasattr(testing_tenant, 'deposit_amount')}")
            print(f"  Deposit amount value: {getattr(testing_tenant, 'deposit_amount', 'NOT FOUND')}")
            print(f"  Deposit amount type: {type(getattr(testing_tenant, 'deposit_amount', None))}")
            
            # Test the exact code from the dialog
            deposit_amount = 0.0
            if hasattr(testing_tenant, 'deposit_amount') and testing_tenant.deposit_amount is not None:
                deposit_amount = float(testing_tenant.deposit_amount)
                print(f"  Converted to float: {deposit_amount}")
            
            deposit_text = f"${deposit_amount:.2f}"
            print(f"  Display text would be: '{deposit_text}'")
            
        else:
            print("❌ Testing Program tenant not found!")
            print("Available tenants:")
            for tid, tenant in tm.tenants.items():
                print(f"  - {tenant.name} (ID: {tid})")
        
    except Exception as e:
        print(f"❌ Error testing tenant loading: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tenant_loading()
