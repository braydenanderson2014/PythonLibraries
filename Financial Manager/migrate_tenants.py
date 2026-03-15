#!/usr/bin/env python3
"""
Migration script to assign existing tenants to admin user.
This ensures existing tenants don't disappear when user filtering is enabled.
"""

from src.tenant import TenantManager
from src.account import AccountManager
from assets.Logger import Logger

logger = Logger()

def migrate_existing_tenants():
    logger.info("MigrateTenants", "Migrating Existing Tenants")
    
    # Create managers
    am = AccountManager()
    tm = TenantManager()
    
    # Find admin user
    admin_username = None
    for username, account in am.accounts.items():
        if account.get('details', {}).get('role') == 'admin':
            admin_username = username
            break
    
    if not admin_username:
        logger.error("MigrateTenants", "No admin user found. Cannot migrate tenants.")
        return
    
    logger.info("MigrateTenants", f"Found admin user: {admin_username}")
    
    # Set admin as current user to see all tenants
    tm.set_current_user(admin_username)
    
    # Find tenants without user_id
    tenants_to_migrate = []
    for tenant in tm.tenants.values():
        if tenant.user_id is None:
            tenants_to_migrate.append(tenant)
    
    logger.info("MigrateTenants", f"Found {len(tenants_to_migrate)} tenants to migrate:")
    
    # Migrate each tenant to admin
    for tenant in tenants_to_migrate:
        logger.debug("MigrateTenants", f"Migrating '{tenant.name}' to admin user")
        tenant.user_id = admin_username
    
    # Save the changes
    tm.save()
    
    logger.info("MigrateTenants", f"Migration complete. {len(tenants_to_migrate)} tenants assigned to admin.")
    
    # Verify migration
    logger.info("MigrateTenants", "Verification:")
    for tenant in tm.list_tenants():
        logger.info("MigrateTenants", f"{tenant.name} (user_id: {tenant.user_id})")

if __name__ == "__main__":
    migrate_existing_tenants()
