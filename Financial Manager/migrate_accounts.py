"""
Account Migration Tool
Migrates user accounts from JSON file to SQLite database
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.account_db import AccountDatabaseManager
    from src.app_paths import ACCOUNT_DB, get_resource_path
    from src.account import AccountManager as JSONAccountManager
except ImportError:
    from account_db import AccountDatabaseManager
    from app_paths import ACCOUNT_DB, get_resource_path
    from account import AccountManager as JSONAccountManager

from assets.Logger import Logger

logger = Logger()


class AccountMigration:
    """
    Handles migration of user accounts from JSON to SQLite database
    """
    
    def __init__(self):
        """Initialize migration tool"""
        self.json_manager = JSONAccountManager()
        self.db_manager = AccountDatabaseManager()
        self.migration_log = []
    
    def validate_json_data(self) -> bool:
        """
        Validate JSON data before migration
        
        Returns:
            True if valid, False otherwise
        """
        logger.info("Validating JSON data...")
        
        if not os.path.exists(ACCOUNT_DB):
            logger.error(f"JSON file not found: {ACCOUNT_DB}")
            return False
        
        try:
            with open(ACCOUNT_DB, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                logger.error("JSON data is not a dictionary")
                return False
            
            user_count = len(data)
            logger.info(f"Found {user_count} users in JSON file")
            
            # Validate each user has required fields
            for username, user_data in data.items():
                if 'account_id' not in user_data:
                    logger.warning(f"User '{username}' missing account_id")
                if 'password_hash' not in user_data:
                    logger.error(f"User '{username}' missing password_hash")
                    return False
            
            logger.info("JSON data validation passed")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating JSON: {e}")
            return False
    
    def backup_database(self) -> str:
        """
        Create backup of existing database
        
        Returns:
            Path to backup file
        """
        db_path = get_resource_path("accounts.db")
        
        if not os.path.exists(db_path):
            logger.info("No existing database to backup")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = get_resource_path(f"accounts_backup_{timestamp}.db")
        
        import shutil
        shutil.copy2(db_path, backup_path)
        
        logger.info(f"Database backed up to: {backup_path}")
        return backup_path
    
    def migrate_users(self, overwrite: bool = False) -> Dict[str, Any]:
        """
        Migrate users from JSON to database
        
        Args:
            overwrite: If True, overwrite existing users in database
            
        Returns:
            Dictionary with migration results
        """
        results = {
            'success': [],
            'failed': [],
            'skipped': [],
            'total': 0,
            'migrated': 0,
            'errors': []
        }
        
        logger.info("Starting user migration...")
        
        # Load JSON data
        accounts = self.json_manager.accounts
        results['total'] = len(accounts)
        
        for username, user_data in accounts.items():
            try:
                # Check if user already exists in database
                existing_user = self.db_manager.get_user_by_username(username)
                
                if existing_user and not overwrite:
                    logger.info(f"User '{username}' already exists in database, skipping")
                    results['skipped'].append(username)
                    continue
                
                # Prepare user data
                account_id = user_data.get('account_id')
                password_hash = user_data.get('password_hash')
                details = user_data.get('details', {})
                
                if existing_user:
                    # Update existing user
                    logger.info(f"Updating existing user: {username}")
                    
                    # Update password if changed
                    if password_hash != existing_user.get('password_hash'):
                        # Note: We can't use change_password() because password_hash is already hashed
                        # We'll update it directly
                        import sqlite3
                        conn = self.db_manager._get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE users 
                            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP 
                            WHERE username = ?
                        """, (password_hash, username))
                        conn.commit()
                        conn.close()
                    
                    # Update details
                    self.db_manager.update_user(username, **details)
                    results['migrated'] += 1
                    results['success'].append(username)
                    logger.info(f"✓ Updated user: {username}")
                    
                else:
                    # Create new user
                    logger.info(f"Creating new user: {username}")
                    
                    # We need to create the user with the existing password hash
                    # This is a special case for migration
                    import sqlite3
                    import json as json_lib
                    
                    conn = self.db_manager._get_connection()
                    cursor = conn.cursor()
                    
                    # Extract known fields from details
                    email = details.get('email')
                    full_name = details.get('full_name')
                    phone = details.get('phone')
                    is_admin = details.get('is_admin', 0)
                    theme_preference = details.get('theme_preference', 'light')
                    currency = details.get('currency', 'USD')
                    timezone = details.get('timezone', 'UTC')
                    language = details.get('language', 'en')
                    
                    # Store remaining details as JSON
                    remaining_details = {k: v for k, v in details.items() 
                                       if k not in ['email', 'full_name', 'phone', 'is_admin', 
                                                  'theme_preference', 'currency', 'timezone', 'language']}
                    details_json = json_lib.dumps(remaining_details) if remaining_details else None
                    
                    cursor.execute("""
                        INSERT INTO users (
                            account_id, username, password_hash, email, full_name, phone,
                            is_admin, theme_preference, currency, timezone, language, details
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (account_id, username, password_hash, email, full_name, phone,
                          is_admin, theme_preference, currency, timezone, language, details_json))
                    
                    conn.commit()
                    conn.close()
                    
                    results['migrated'] += 1
                    results['success'].append(username)
                    logger.info(f"✓ Migrated user: {username}")
                
            except Exception as e:
                error_msg = f"Error migrating user '{username}': {e}"
                logger.error(error_msg)
                results['failed'].append(username)
                results['errors'].append(error_msg)
        
        logger.info(f"""
Migration complete:
- Total users: {results['total']}
- Migrated: {results['migrated']}
- Skipped: {len(results['skipped'])}
- Failed: {len(results['failed'])}
""")
        
        return results
    
    def verify_migration(self) -> Dict[str, Any]:
        """
        Verify that all users were migrated correctly
        
        Returns:
            Dictionary with verification results
        """
        results = {
            'verified': [],
            'missing': [],
            'mismatched': [],
            'total_json': 0,
            'total_db': 0
        }
        
        logger.info("Verifying migration...")
        
        # Get all JSON users
        json_accounts = self.json_manager.accounts
        results['total_json'] = len(json_accounts)
        
        # Get all DB users
        db_users = self.db_manager.list_users(active_only=False)
        results['total_db'] = len(db_users)
        
        # Check each JSON user exists in DB
        for username, json_data in json_accounts.items():
            db_user = self.db_manager.get_user_by_username(username)
            
            if not db_user:
                results['missing'].append(username)
                logger.warning(f"User '{username}' not found in database")
                continue
            
            # Verify password hash matches
            if json_data.get('password_hash') != db_user.get('password_hash'):
                results['mismatched'].append(username)
                logger.warning(f"Password hash mismatch for user '{username}'")
                continue
            
            results['verified'].append(username)
        
        logger.info(f"""
Verification results:
- JSON users: {results['total_json']}
- DB users: {results['total_db']}
- Verified: {len(results['verified'])}
- Missing: {len(results['missing'])}
- Mismatched: {len(results['mismatched'])}
""")
        
        return results
    
    def generate_report(self, migration_results: Dict[str, Any], 
                       verification_results: Dict[str, Any]) -> str:
        """
        Generate migration report
        
        Args:
            migration_results: Results from migrate_users()
            verification_results: Results from verify_migration()
            
        Returns:
            Report as string
        """
        report = f"""
{'='*70}
ACCOUNT MIGRATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}

MIGRATION SUMMARY:
-----------------
Total users in JSON:     {migration_results['total']}
Successfully migrated:   {migration_results['migrated']}
Skipped (existing):      {len(migration_results['skipped'])}
Failed:                  {len(migration_results['failed'])}

VERIFICATION SUMMARY:
--------------------
Total users in JSON:     {verification_results['total_json']}
Total users in DB:       {verification_results['total_db']}
Verified:                {len(verification_results['verified'])}
Missing from DB:         {len(verification_results['missing'])}
Password mismatches:     {len(verification_results['mismatched'])}

"""
        
        if migration_results['success']:
            report += "\nSUCCESSFULLY MIGRATED USERS:\n"
            for username in migration_results['success']:
                report += f"  ✓ {username}\n"
        
        if migration_results['skipped']:
            report += "\nSKIPPED USERS (already in DB):\n"
            for username in migration_results['skipped']:
                report += f"  - {username}\n"
        
        if migration_results['failed']:
            report += "\nFAILED MIGRATIONS:\n"
            for username in migration_results['failed']:
                report += f"  ✗ {username}\n"
        
        if migration_results['errors']:
            report += "\nERRORS:\n"
            for error in migration_results['errors']:
                report += f"  ! {error}\n"
        
        if verification_results['missing']:
            report += "\nMISSING FROM DATABASE:\n"
            for username in verification_results['missing']:
                report += f"  ! {username}\n"
        
        if verification_results['mismatched']:
            report += "\nPASSWORD MISMATCHES:\n"
            for username in verification_results['mismatched']:
                report += f"  ! {username}\n"
        
        report += f"\n{'='*70}\n"
        
        return report


def main():
    """Main migration function"""
    logger.info("MigrateAccounts", "="*70)
    logger.info("MigrateAccounts", "FINANCIAL MANAGER - ACCOUNT MIGRATION TOOL")
    logger.info("MigrateAccounts", "Migrate user accounts from JSON to SQLite database")
    logger.info("MigrateAccounts", "="*70)
    
    migration = AccountMigration()
    
    # Validate JSON data
    logger.info("MigrateAccounts", "Step 1: Validating JSON data...")
    if not migration.validate_json_data():
        logger.error("MigrateAccounts", "Validation failed. Please fix errors and try again.")
        return
    logger.info("MigrateAccounts", "Validation passed")
    
    # Backup existing database
    logger.info("MigrateAccounts", "Step 2: Creating database backup...")
    backup_path = migration.backup_database()
    if backup_path:
        logger.info("MigrateAccounts", f"Backup created: {backup_path}")
    else:
        logger.info("MigrateAccounts", "No existing database to backup")
    
    # Confirm migration
    logger.info("MigrateAccounts", "Step 3: Ready to migrate users")
    response = input("Overwrite existing users in database? (y/N): ").strip().lower()
    overwrite = response == 'y'
    
    logger.info("MigrateAccounts", "Starting migration...")
    
    # Migrate users
    migration_results = migration.migrate_users(overwrite=overwrite)
    
    # Verify migration
    logger.info("MigrateAccounts", "Verifying migration...")
    verification_results = migration.verify_migration()
    
    # Generate report
    report = migration.generate_report(migration_results, verification_results)
    logger.info("MigrateAccounts", report)
    
    # Save report to file
    report_path = get_resource_path(f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info("MigrateAccounts", f"Report saved to: {report_path}")
    
    # Summary
    if len(migration_results['failed']) == 0 and len(verification_results['missing']) == 0:
        logger.info("MigrateAccounts", "Migration completed successfully!")
    elif len(migration_results['failed']) > 0:
        logger.warning("MigrateAccounts", f"Migration completed with {len(migration_results['failed'])} errors")
    else:
        logger.warning("MigrateAccounts", "Migration completed but verification found issues")


if __name__ == '__main__':
    main()
