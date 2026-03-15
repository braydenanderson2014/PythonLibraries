#!/usr/bin/env python3
"""Standalone test for the deposit dialog with actual tenant data."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_dialog_with_real_data():
    print("=== Testing Dialog with Real Tenant Data ===")
    
    try:
        from src.tenant import TenantManager
        
        # Load real tenant data
        tm = TenantManager()
        tm.load()
        
        # Find Testing Program tenant
        testing_tenant = None
        for tid, tenant in tm.tenants.items():
            if tenant.name == "Testing Program":
                testing_tenant = tenant
                break
        
        if not testing_tenant:
            print("❌ Testing Program tenant not found!")
            return
        
        print(f"✅ Found tenant: {testing_tenant.name}")
        print(f"   Deposit amount: ${testing_tenant.deposit_amount:.2f}")
        
        # Simulate what the dialog constructor should do
        print("\n--- Simulating Dialog Initialization ---")
        print(f"Tenant object: {testing_tenant}")
        print(f"Tenant name: {testing_tenant.name}")
        print(f"Tenant ID: {testing_tenant.tenant_id}")
        print(f"Has deposit_amount: {hasattr(testing_tenant, 'deposit_amount')}")
        print(f"Deposit amount value: {testing_tenant.deposit_amount}")
        print(f"Deposit amount type: {type(testing_tenant.deposit_amount)}")
        
        # Simulate load_tenant_data logic
        print("\n--- Simulating load_tenant_data ---")
        deposit_amount = 0.0
        
        if hasattr(testing_tenant, 'deposit_amount') and testing_tenant.deposit_amount is not None:
            deposit_amount = float(testing_tenant.deposit_amount)
            print(f"✅ Loaded deposit amount: {deposit_amount}")
        else:
            print("❌ No deposit_amount found")
        
        deposit_text = f"${deposit_amount:.2f}"
        print(f"✅ Display text: '{deposit_text}'")
        
        # This should show $1000.00
        if deposit_text == "$1000.00":
            print("✅ Correct! Should display $1000.00")
        else:
            print(f"❌ Wrong! Expected $1000.00, got {deposit_text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dialog_with_real_data()
