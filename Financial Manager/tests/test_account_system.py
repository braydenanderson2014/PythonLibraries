"""
Test Account Database System
Comprehensive tests for JSON and database backends
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.account_unified import UnifiedAccountManager
from src.account_db import AccountDatabaseManager
from src.app_paths import get_resource_path
import json


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")


def test_database_backend():
    """Test database backend operations"""
    print_header("Testing Database Backend")
    
    try:
        # Create manager with database backend
        manager = UnifiedAccountManager(backend='database')
        print_success("Database backend initialized")
        
        # Test 1: Create account
        print("\n1. Testing account creation...")
        try:
            user = manager.create_account(
                'testuser_db',
                'TestPassword123!',
                email='testuser@example.com',
                full_name='Test User DB',
                phone='555-1234'
            )
            print_success(f"Created account: {user['username']} (ID: {user['account_id']})")
        except ValueError as e:
            if 'already exists' in str(e):
                print_info(f"Account already exists, updating instead")
                manager.update_account('testuser_db', 
                    email='testuser@example.com',
                    full_name='Test User DB Updated'
                )
                user = manager.get_account('testuser_db')
            else:
                raise
        
        # Test 2: Get account
        print("\n2. Testing account retrieval...")
        retrieved = manager.get_account('testuser_db')
        if retrieved and retrieved['username'] == 'testuser_db':
            print_success(f"Retrieved account: {retrieved['username']}")
            print(f"   Email: {retrieved.get('email')}")
            print(f"   Full name: {retrieved.get('full_name')}")
        else:
            print_error("Failed to retrieve account")
        
        # Test 3: Verify password
        print("\n3. Testing password verification...")
        if manager.verify_password('testuser_db', 'TestPassword123!'):
            print_success("Password verification successful")
        else:
            print_error("Password verification failed")
        
        # Test 4: Update account
        print("\n4. Testing account update...")
        manager.update_account('testuser_db', 
            phone='555-5678',
            theme_preference='dark'
        )
        updated = manager.get_account('testuser_db')
        if updated['phone'] == '555-5678':
            print_success("Account updated successfully")
            print(f"   New phone: {updated['phone']}")
        else:
            print_error("Account update failed")
        
        # Test 5: Change password
        print("\n5. Testing password change...")
        manager.change_password('testuser_db', 'NewPassword456!')
        if manager.verify_password('testuser_db', 'NewPassword456!'):
            print_success("Password changed successfully")
        else:
            print_error("Password change failed")
        
        # Change it back for consistency
        manager.change_password('testuser_db', 'TestPassword123!')
        
        # Test 6: List accounts
        print("\n6. Testing account listing...")
        accounts = manager.list_accounts()
        print_success(f"Found {len(accounts)} accounts")
        for username in accounts[:5]:  # Show first 5
            print(f"   - {username}")
        
        # Test 7: Get stats
        print("\n7. Testing statistics...")
        stats = manager.get_stats()
        print_success("Statistics retrieved:")
        print(f"   Total users: {stats.get('total_users', 0)}")
        print(f"   Active users: {stats.get('active_users', 0)}")
        print(f"   Database size: {stats.get('db_size', 0)} bytes")
        
        return True
        
    except Exception as e:
        print_error(f"Database backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_json_backend():
    """Test JSON backend operations"""
    print_header("Testing JSON Backend")
    
    try:
        # Create manager with JSON backend
        manager = UnifiedAccountManager(backend='json')
        print_success("JSON backend initialized")
        
        # Test 1: Create account
        print("\n1. Testing account creation...")
        try:
            user = manager.create_account(
                'testuser_json',
                'TestPassword123!',
                email='testuser_json@example.com',
                full_name='Test User JSON'
            )
            print_success(f"Created account: {user['username']} (ID: {user['account_id']})")
        except ValueError as e:
            if 'already exists' in str(e):
                print_info("Account already exists, continuing with tests")
                user = manager.get_account('testuser_json')
            else:
                raise
        
        # Test 2: Get account
        print("\n2. Testing account retrieval...")
        retrieved = manager.get_account('testuser_json')
        if retrieved and retrieved['username'] == 'testuser_json':
            print_success(f"Retrieved account: {retrieved['username']}")
        else:
            print_error("Failed to retrieve account")
        
        # Test 3: Verify password
        print("\n3. Testing password verification...")
        if manager.verify_password('testuser_json', 'TestPassword123!'):
            print_success("Password verification successful")
        else:
            print_error("Password verification failed")
        
        # Test 4: Update account
        print("\n4. Testing account update...")
        manager.update_account('testuser_json', phone='555-9999')
        updated = manager.get_account('testuser_json')
        if updated['details'].get('phone') == '555-9999':
            print_success("Account updated successfully")
        else:
            print_error("Account update failed")
        
        # Test 5: List accounts
        print("\n5. Testing account listing...")
        accounts = manager.list_accounts()
        print_success(f"Found {len(accounts)} accounts")
        
        # Test 6: Get stats
        print("\n6. Testing statistics...")
        stats = manager.get_stats()
        print_success("Statistics retrieved:")
        print(f"   Backend: {stats.get('backend')}")
        print(f"   Total users: {stats.get('total_users', 0)}")
        print(f"   File size: {stats.get('file_size', 0)} bytes")
        
        return True
        
    except Exception as e:
        print_error(f"JSON backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backend_switching():
    """Test switching between backends"""
    print_header("Testing Backend Switching")
    
    try:
        # Start with JSON
        print("1. Starting with JSON backend...")
        manager = UnifiedAccountManager(backend='json')
        print_success(f"Current backend: {manager.backend}")
        
        # Get JSON user count
        json_accounts = manager.list_accounts()
        print(f"   JSON accounts: {len(json_accounts)}")
        
        # Switch to database
        print("\n2. Switching to database backend...")
        manager.set_backend('database', save_config=False)
        print_success(f"Current backend: {manager.backend}")
        
        # Get database user count
        db_accounts = manager.list_accounts()
        print(f"   Database accounts: {len(db_accounts)}")
        
        # Switch back to JSON
        print("\n3. Switching back to JSON backend...")
        manager.set_backend('json', save_config=False)
        print_success(f"Current backend: {manager.backend}")
        
        return True
        
    except Exception as e:
        print_error(f"Backend switching test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_detection():
    """Test automatic backend detection"""
    print_header("Testing Auto-Detection")
    
    try:
        # Create manager without specifying backend
        print("Creating manager without specifying backend...")
        manager = UnifiedAccountManager()
        print_success(f"Auto-detected backend: {manager.backend}")
        
        # Show stats
        stats = manager.get_stats()
        print(f"   Total users: {stats.get('total_users', 0)}")
        
        return True
        
    except Exception as e:
        print_error(f"Auto-detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compatibility():
    """Test backward compatibility"""
    print_header("Testing Backward Compatibility")
    
    try:
        # Test legacy import
        print("1. Testing legacy AccountManager import...")
        from src.account import AccountManager as LegacyManager
        legacy = LegacyManager()
        print_success("Legacy AccountManager loaded")
        
        # Test compatibility
        print("\n2. Testing legacy operations...")
        accounts = legacy.accounts if hasattr(legacy, 'accounts') else {}
        print_success(f"Legacy manager has {len(accounts)} accounts")
        
        # Test new unified manager
        print("\n3. Testing UnifiedAccountManager compatibility...")
        from src.account_unified import AccountManager as NewManager
        new_manager = NewManager()
        print_success(f"New AccountManager backend: {new_manager.backend}")
        
        return True
        
    except Exception as e:
        print_error(f"Compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_comparison():
    """Show comparison between JSON and database"""
    print_header("Backend Comparison")
    
    try:
        # JSON stats
        json_manager = UnifiedAccountManager(backend='json')
        json_stats = json_manager.get_stats()
        
        # Database stats
        db_manager = UnifiedAccountManager(backend='database')
        db_stats = db_manager.get_stats()
        
        print(f"{Colors.BOLD}JSON Backend:{Colors.END}")
        print(f"  Users: {json_stats.get('total_users', 0)}")
        print(f"  File: {json_stats.get('file_path', 'N/A')}")
        print(f"  Size: {json_stats.get('file_size', 0)} bytes")
        
        print(f"\n{Colors.BOLD}Database Backend:{Colors.END}")
        print(f"  Total users: {db_stats.get('total_users', 0)}")
        print(f"  Active users: {db_stats.get('active_users', 0)}")
        print(f"  Database: {db_stats.get('db_path', 'N/A')}")
        print(f"  Size: {db_stats.get('db_size', 0)} bytes")
        
    except Exception as e:
        print_error(f"Error showing comparison: {e}")


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║         FINANCIAL MANAGER - ACCOUNT SYSTEM TEST SUITE              ║")
    print("║                Database Migration & Backend Testing                  ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(Colors.END)
    
    results = {}
    
    # Run tests
    results['Database Backend'] = test_database_backend()
    results['JSON Backend'] = test_json_backend()
    results['Backend Switching'] = test_backend_switching()
    results['Auto-Detection'] = test_auto_detection()
    results['Compatibility'] = test_compatibility()
    
    # Show comparison
    show_comparison()
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.END}")
        return 1


if __name__ == '__main__':
    exit(main())
