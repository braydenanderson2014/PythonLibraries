#!/usr/bin/env python3
"""
Test script to verify user-based tenant filtering functionality.
"""

from src.tenant import TenantManager
from src.account import AccountManager

def test_user_filtering():
    print("=== Testing User-Based Tenant Filtering ===")
    
    # Create managers
    am = AccountManager()
    tm = TenantManager()
    
    # Test tenant filtering for regular user
    print("\n1. Testing regular user access:")
    tm.set_current_user('braydenanderson2014')
    print(f'Current user ID: {tm.current_user_id}')
    print(f'Is admin: {tm.is_admin()}')
    
    # List tenants for this user
    tenants = tm.list_tenants()
    print(f'Tenants for {tm.current_user_id}: {len(tenants)} tenants')
    for tenant in tenants:
        print(f'  - {tenant.name} (user_id: {tenant.user_id})')
    
    # Test admin access
    print("\n2. Testing admin access:")
    admin_users = [acc for acc in am.accounts.values() if acc.get('details', {}).get('role') == 'admin']
    if admin_users:
        admin_username = list(admin_users)[0]['username']
        tm.set_current_user(admin_username)
        print(f'Switching to admin user: {admin_username}')
        print(f'Is admin: {tm.is_admin()}')
        
        all_tenants = tm.list_tenants()
        print(f'All tenants for admin: {len(all_tenants)} tenants')
        for tenant in all_tenants:
            print(f'  - {tenant.name} (user_id: {tenant.user_id})')
    else:
        print('No admin users found')
    
    # Test creating a tenant with user assignment
    print("\n3. Testing tenant creation with user assignment:")
    tm.set_current_user('braydenanderson2014')
    
    # Check if we can add a test tenant
    test_tenant = tm.add_tenant(
        name="Test User Tenant",
        rental_period=("2024-01-01", "2024-12-31"),
        rent_amount=1000.0,
        deposit_amount=2000.0,
        contact_info={'email': 'test@example.com'},
        notes="Test tenant for user filtering"
    )
    
    print(f'Created test tenant: {test_tenant.name} with user_id: {test_tenant.user_id}')
    
    # Verify it shows up only for that user
    user_tenants = tm.list_tenants()
    print(f'Tenants after creation for {tm.current_user_id}: {len(user_tenants)} tenants')
    
    # Switch to admin and verify it shows up
    if admin_users:
        tm.set_current_user(admin_username)
        admin_tenants = tm.list_tenants()
        print(f'All tenants visible to admin: {len(admin_tenants)} tenants')
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_user_filtering()
