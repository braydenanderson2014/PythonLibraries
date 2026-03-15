"""
Account Management CLI Tool
Command-line interface for managing user accounts and backends
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.account_unified import UnifiedAccountManager
from src.app_paths import get_resource_path
import json


def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_menu():
    """Print main menu"""
    print("\n" + "="*70)
    print("  FINANCIAL MANAGER - ACCOUNT MANAGEMENT TOOL")
    print("="*70)
    print("\n1.  List all accounts")
    print("2.  Create new account")
    print("3.  View account details")
    print("4.  Update account")
    print("5.  Change password")
    print("6.  Delete account")
    print("7.  Verify password")
    print("8.  Show statistics")
    print("9.  Switch backend")
    print("10. View current backend")
    print("11. Run migration")
    print("12. Run tests")
    print("0.  Exit")
    print()


def list_accounts(manager):
    """List all accounts"""
    print_header("User Accounts")
    
    accounts = manager.list_accounts(active_only=False)
    
    if not accounts:
        print("No accounts found.")
        return
    
    print(f"Total accounts: {len(accounts)}\n")
    
    for i, username in enumerate(accounts, 1):
        account = manager.get_account(username)
        status = "✓ Active" if account.get('is_active', 1) else "✗ Inactive"
        admin = "👑 Admin" if account.get('is_admin', 0) else ""
        print(f"{i:3}. {username:20} {status:12} {admin}")


def create_account(manager):
    """Create new account"""
    print_header("Create New Account")
    
    username = input("Username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return
    
    password = input("Password: ").strip()
    if not password:
        print("❌ Password cannot be empty")
        return
    
    # Optional details
    email = input("Email (optional): ").strip() or None
    full_name = input("Full name (optional): ").strip() or None
    phone = input("Phone (optional): ").strip() or None
    
    is_admin = input("Admin user? (y/N): ").strip().lower() == 'y'
    
    try:
        user = manager.create_account(
            username, 
            password,
            email=email,
            full_name=full_name,
            phone=phone,
            is_admin=1 if is_admin else 0
        )
        print(f"\n✓ Account created successfully!")
        print(f"  Username: {user.get('username')}")
        print(f"  Account ID: {user.get('account_id')}")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


def view_account(manager):
    """View account details"""
    print_header("View Account Details")
    
    username = input("Username: ").strip()
    account = manager.get_account(username)
    
    if not account:
        print(f"❌ Account '{username}' not found")
        return
    
    print(f"\nAccount Details:")
    print(f"  Username:     {account.get('username')}")
    print(f"  Account ID:   {account.get('account_id')}")
    print(f"  Email:        {account.get('email', 'N/A')}")
    print(f"  Full name:    {account.get('full_name', 'N/A')}")
    print(f"  Phone:        {account.get('phone', 'N/A')}")
    print(f"  Active:       {'Yes' if account.get('is_active', 1) else 'No'}")
    print(f"  Admin:        {'Yes' if account.get('is_admin', 0) else 'No'}")
    print(f"  Created:      {account.get('created_at', 'N/A')}")
    print(f"  Last login:   {account.get('last_login', 'Never')}")
    print(f"  Theme:        {account.get('theme_preference', 'default')}")
    print(f"  Currency:     {account.get('currency', 'USD')}")
    
    # Additional details
    if account.get('details'):
        print(f"\n  Additional details:")
        details = account['details']
        for key, value in details.items():
            print(f"    {key}: {value}")


def update_account(manager):
    """Update account details"""
    print_header("Update Account")
    
    username = input("Username: ").strip()
    account = manager.get_account(username)
    
    if not account:
        print(f"❌ Account '{username}' not found")
        return
    
    print(f"\nCurrent details for '{username}':")
    print(f"  Email:     {account.get('email', 'N/A')}")
    print(f"  Full name: {account.get('full_name', 'N/A')}")
    print(f"  Phone:     {account.get('phone', 'N/A')}")
    
    print("\nEnter new values (leave blank to keep current):")
    
    updates = {}
    
    email = input(f"Email [{account.get('email', '')}]: ").strip()
    if email:
        updates['email'] = email
    
    full_name = input(f"Full name [{account.get('full_name', '')}]: ").strip()
    if full_name:
        updates['full_name'] = full_name
    
    phone = input(f"Phone [{account.get('phone', '')}]: ").strip()
    if phone:
        updates['phone'] = phone
    
    if updates:
        try:
            manager.update_account(username, **updates)
            print("\n✓ Account updated successfully!")
        except Exception as e:
            print(f"\n❌ Error updating account: {e}")
    else:
        print("\n⚠ No changes made")


def change_password(manager):
    """Change user password"""
    print_header("Change Password")
    
    username = input("Username: ").strip()
    account = manager.get_account(username)
    
    if not account:
        print(f"❌ Account '{username}' not found")
        return
    
    new_password = input("New password: ").strip()
    if not new_password:
        print("❌ Password cannot be empty")
        return
    
    confirm = input("Confirm password: ").strip()
    if new_password != confirm:
        print("❌ Passwords do not match")
        return
    
    try:
        manager.change_password(username, new_password)
        print("\n✓ Password changed successfully!")
    except Exception as e:
        print(f"\n❌ Error changing password: {e}")


def delete_account(manager):
    """Delete account"""
    print_header("Delete Account")
    
    username = input("Username: ").strip()
    account = manager.get_account(username)
    
    if not account:
        print(f"❌ Account '{username}' not found")
        return
    
    print(f"\n⚠️  WARNING: This will permanently delete account '{username}'")
    confirm = input("Type username to confirm: ").strip()
    
    if confirm != username:
        print("❌ Confirmation failed. Account not deleted.")
        return
    
    try:
        manager.delete_account(username)
        print("\n✓ Account deleted successfully!")
    except Exception as e:
        print(f"\n❌ Error deleting account: {e}")


def verify_password(manager):
    """Verify user password"""
    print_header("Verify Password")
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    if manager.verify_password(username, password):
        print("\n✓ Password is correct!")
    else:
        print("\n❌ Invalid username or password")


def show_stats(manager):
    """Show account statistics"""
    print_header("Account Statistics")
    
    stats = manager.get_stats()
    
    print(f"Backend:        {manager.backend.upper()}")
    print(f"Total users:    {stats.get('total_users', 0)}")
    
    if manager.backend == 'database':
        print(f"Active users:   {stats.get('active_users', 0)}")
        print(f"Admin users:    {stats.get('admin_users', 0)}")
        print(f"Recent logins:  {stats.get('recent_logins', 0)} (last 30 days)")
        print(f"Database path:  {stats.get('db_path', 'N/A')}")
        print(f"Database size:  {stats.get('db_size', 0)} bytes")
    else:
        print(f"File path:      {stats.get('file_path', 'N/A')}")
        print(f"File size:      {stats.get('file_size', 0)} bytes")


def switch_backend(manager):
    """Switch storage backend"""
    print_header("Switch Backend")
    
    print(f"Current backend: {manager.backend.upper()}\n")
    print("1. JSON (file-based)")
    print("2. Database (SQLite)")
    print("0. Cancel")
    
    choice = input("\nSelect backend: ").strip()
    
    if choice == '1':
        new_backend = 'json'
    elif choice == '2':
        new_backend = 'database'
    else:
        print("❌ Cancelled")
        return
    
    if new_backend == manager.backend:
        print(f"⚠️  Already using {new_backend} backend")
        return
    
    save_config = input("Save to config file? (Y/n): ").strip().lower() != 'n'
    
    try:
        manager.set_backend(new_backend, save_config=save_config)
        print(f"\n✓ Switched to {new_backend.upper()} backend")
        if save_config:
            print("✓ Configuration saved")
    except Exception as e:
        print(f"\n❌ Error switching backend: {e}")


def view_backend(manager):
    """View current backend"""
    print_header("Current Backend")
    
    print(f"Backend: {manager.backend.upper()}\n")
    
    # Check config file
    config_path = get_resource_path("account_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                print(f"Config file: {config_path}")
                print(f"Configured backend: {config.get('backend', 'N/A')}")
        except Exception as e:
            print(f"⚠️  Error reading config: {e}")
    else:
        print("Config file: Not found (using auto-detection)")
    
    print(f"\nBackend detection priority:")
    print(f"  1. Config file (account_config.json)")
    print(f"  2. Database existence check")
    print(f"  3. Default to JSON")


def run_migration():
    """Run migration tool"""
    print_header("Run Migration")
    
    print("This will run the account migration tool.")
    confirm = input("Continue? (Y/n): ").strip().lower()
    
    if confirm == 'n':
        print("❌ Cancelled")
        return
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'migrate_accounts.py'],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            print("\n✓ Migration completed")
        else:
            print(f"\n❌ Migration failed with code {result.returncode}")
    except Exception as e:
        print(f"\n❌ Error running migration: {e}")


def run_tests():
    """Run test suite"""
    print_header("Run Tests")
    
    print("This will run the account system test suite.")
    confirm = input("Continue? (Y/n): ").strip().lower()
    
    if confirm == 'n':
        print("❌ Cancelled")
        return
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'test_account_system.py'],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")


def main():
    """Main menu loop"""
    # Initialize manager
    manager = UnifiedAccountManager()
    
    while True:
        print_menu()
        choice = input("Select option: ").strip()
        
        if choice == '1':
            list_accounts(manager)
        elif choice == '2':
            create_account(manager)
        elif choice == '3':
            view_account(manager)
        elif choice == '4':
            update_account(manager)
        elif choice == '5':
            change_password(manager)
        elif choice == '6':
            delete_account(manager)
        elif choice == '7':
            verify_password(manager)
        elif choice == '8':
            show_stats(manager)
        elif choice == '9':
            switch_backend(manager)
        elif choice == '10':
            view_backend(manager)
        elif choice == '11':
            run_migration()
        elif choice == '12':
            run_tests()
        elif choice == '0':
            print("\nGoodbye!")
            break
        else:
            print("\n❌ Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
