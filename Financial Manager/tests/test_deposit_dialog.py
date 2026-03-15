#!/usr/bin/env python3
"""Test script for the deposit amount dialog."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.tenant import Tenant

def test_deposit_dialog():
    print("=== Testing Deposit Amount Dialog ===")
    
    # Create a test tenant
    test_tenant = Tenant(
        name="Testing Program",
        rental_period=("2024-01-01", "2024-12-31"),
        rent_amount=1200.0,
        deposit_amount=2400.0,  # Set a deposit amount
        tenant_id="JV6WCpRzr6",
        user_id="test_user"
    )
    
    print(f"Test tenant created:")
    print(f"  Name: {test_tenant.name}")
    print(f"  Tenant ID: {test_tenant.tenant_id}")
    print(f"  Deposit Amount: ${test_tenant.deposit_amount:.2f}")
    print(f"  Has deposit_amount attribute: {hasattr(test_tenant, 'deposit_amount')}")
    
    # Try importing the dialog
    try:
        from ui.deposit_amount_dialog import DepositAmountDialog
        print("✅ DepositAmountDialog imported successfully")
        
        # Test dialog creation (without actually showing it since we don't have Qt app)
        print("\nDialog would be created with:")
        print(f"  Tenant: {test_tenant.name}")
        print(f"  Current deposit: ${test_tenant.deposit_amount:.2f}")
        print("  Debug output should show proper deposit loading")
        
    except Exception as e:
        print(f"❌ Error testing dialog: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deposit_dialog()
