#!/usr/bin/env python3
"""
Test script for account migration functionality.
Tests automatic detection and migration of credentials from JSON to database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.account_migration import AccountMigration, auto_migrate_on_login
from src.account import AccountManager as JSONAccountManager
from src.account_db import AccountDatabaseManager
from assets.Logger import Logger

logger = Logger()


def test_migration_detection():
    """Test detection of where a user's credentials are stored"""
    print("\n" + "="*60)
    print("TEST 1: Migration Detection")
    print("="*60)
    
    migration = AccountMigration()
    
    # Get migration status
    status = migration.get_migration_status()
    
    print(f"\nMigration Status:")
    print(f"  JSON Users: {status['json_total']}")
    print(f"  Database Users: {status['database_total']}")
    print(f"  Users in both: {status['in_both']}")
    print(f"  JSON-only users: {status['json_only']}")
    print(f"  Database-only users: {status['database_only']}")
    print(f"  Needs migration: {status['needs_migration']}")
    
    return status


def test_single_user_migration(username: str):
    """Test migrating a single user from JSON to database"""
    print("\n" + "="*60)
    print(f"TEST 2: Single User Migration ({username})")
    print("="*60)
    
    migration = AccountMigration()
    
    # Detect source
    source = migration.detect_login_source(username)
    print(f"\nDetected login source for '{username}': {source}")
    
    if source == 'json':
        # Check if already in database
        in_db = migration.is_hash_in_database(username)
        print(f"User hash in database: {in_db}")
        
        # Perform migration
        print(f"\nAttempting migration for '{username}'...")
        success, message = migration.migrate_json_to_database(username)
        print(f"Migration result: {message}")
        
        if success:
            # Verify cleanup
            print(f"\nVerifying cleanup...")
            verified, verify_message = migration.verify_migration_cleanup(username)
            print(f"Cleanup verification: {verify_message}")
            
            if verified:
                print("✓ Migration and cleanup successful!")
            else:
                print("✗ Migration succeeded but cleanup verification failed!")
                return False
        
        # Check final source
        final_source = migration.detect_login_source(username)
        print(f"Final login source: {final_source}")
        
        return success and verified
    else:
        print(f"User {username} is not in JSON storage, skipping migration test")
        return False


def test_auto_migrate_on_login(username: str):
    """Test the auto_migrate_on_login convenience function"""
    print("\n" + "="*60)
    print(f"TEST 3: Auto-Migration on Login ({username})")
    print("="*60)
    
    migration = AccountMigration()
    initial_source = migration.detect_login_source(username)
    print(f"\nInitial source for '{username}': {initial_source}")
    
    # Call auto migrate
    result = auto_migrate_on_login(username)
    print(f"Auto-migration result: {result}")
    
    # Check final source
    final_source = migration.detect_login_source(username)
    print(f"Final source for '{username}': {final_source}")
    
    return result


def test_migrate_all():
    """Test migrating all JSON users to database"""
    print("\n" + "="*60)
    print("TEST 4: Migrate All JSON Users")
    print("="*60)
    
    migration = AccountMigration()
    
    print("\nStarting full migration...")
    results = migration.migrate_all_json_users()
    
    print("\nMigration Results:")
    successful_migrations = 0
    verified_migrations = 0
    
    for username, result in results.items():
        status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
        print(f"  {username}: {status}")
        print(f"    Message: {result['message']}")
        
        if result['success']:
            successful_migrations += 1
            
            # Verify cleanup
            verified, verify_msg = migration.verify_migration_cleanup(username)
            if verified:
                print(f"    ✓ Cleanup verified")
                verified_migrations += 1
            else:
                print(f"    ✗ Cleanup verification failed: {verify_msg}")
    
    # Get final status
    status = migration.get_migration_status()
    print(f"\nFinal Status:")
    print(f"  JSON Users Remaining: {status['json_total']}")
    print(f"  Database Users: {status['database_total']}")
    print(f"  Needs migration: {status['needs_migration']}")
    
    print(f"\nMigration Summary:")
    print(f"  Total migrations attempted: {len(results)}")
    print(f"  Successful migrations: {successful_migrations}")
    print(f"  Verified cleanups: {verified_migrations}")
    
    return all(r['success'] for r in results.values())


def print_menu():
    """Print test menu"""
    print("\n" + "="*60)
    print("Account Migration Test Menu")
    print("="*60)
    print("1. Check migration status")
    print("2. Test single user migration (enter username)")
    print("3. Test auto-migration on login (enter username)")
    print("4. Migrate all JSON users to database")
    print("5. Exit")
    print("="*60)


def main():
    """Main test runner"""
    print("\nAccount Migration Test Suite")
    print("This tool tests automatic migration of credentials from JSON to database")
    
    while True:
        print_menu()
        choice = input("\nSelect test (1-5): ").strip()
        
        if choice == '1':
            test_migration_detection()
        
        elif choice == '2':
            username = input("Enter username to migrate: ").strip()
            if username:
                test_single_user_migration(username)
            else:
                print("Invalid username")
        
        elif choice == '3':
            username = input("Enter username for auto-migration test: ").strip()
            if username:
                test_auto_migrate_on_login(username)
            else:
                print("Invalid username")
        
        elif choice == '4':
            confirm = input("Migrate ALL JSON users to database? (yes/no): ").strip().lower()
            if confirm == 'yes':
                test_migrate_all()
            else:
                print("Migration cancelled")
        
        elif choice == '5':
            print("Exiting...")
            break
        
        else:
            print("Invalid choice, please try again")


if __name__ == '__main__':
    main()
