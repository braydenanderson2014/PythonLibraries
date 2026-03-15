#!/usr/bin/env python3
"""
Migration script to normalize all tenant account_status values to lowercase.
This script updates the tenants.json file to ensure consistency.
"""

import json
import os
from pathlib import Path

def normalize_tenant_status():
    """Normalize all tenant account_status values to lowercase in tenants.json"""
    
    # Find the tenants.json file
    script_dir = Path(__file__).parent
    tenant_file = script_dir / 'tenants.json'
    
    if not tenant_file.exists():
        print(f"❌ tenants.json not found at: {tenant_file}")
        return False
    
    print(f"📂 Found tenants.json at: {tenant_file}")
    
    # Backup the original file
    backup_file = script_dir / 'tenants.json.backup'
    try:
        with open(tenant_file, 'r') as f:
            data = json.load(f)
        
        # Create backup
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Backup created at: {backup_file}")
        
    except Exception as e:
        print(f"❌ Error reading tenants.json: {e}")
        return False
    
    # Process tenants
    updated_count = 0
    total_count = 0
    
    for user_id, user_data in data.items():
        if isinstance(user_data, dict) and 'tenants' in user_data:
            for tenant in user_data['tenants']:
                total_count += 1
                if 'account_status' in tenant:
                    old_status = tenant['account_status']
                    new_status = old_status.lower() if old_status else 'active'
                    
                    if old_status != new_status:
                        tenant['account_status'] = new_status
                        updated_count += 1
                        print(f"  📝 Updated tenant '{tenant.get('name', 'Unknown')}': '{old_status}' → '{new_status}'")
    
    # Save the updated data
    try:
        with open(tenant_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✅ Successfully normalized {updated_count} of {total_count} tenants")
        print(f"📁 Original file backed up to: {backup_file}")
        
        if updated_count == 0:
            print("ℹ️  All tenant statuses were already lowercase")
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing updated data: {e}")
        print(f"⚠️  Your data is safe in the backup: {backup_file}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Tenant Status Normalization Script")
    print("=" * 60)
    print("\nThis script will normalize all account_status values to lowercase.")
    print("A backup will be created automatically.\n")
    
    success = normalize_tenant_status()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Migration failed. Check errors above.")
        print("=" * 60)
