#!/usr/bin/env python3
"""
Test script for the enhanced financial tracker features
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.bank import Bank

def test_bank_dashboard_data():
    """Test that we can retrieve bank data for dashboards"""
    print("Testing bank dashboard data retrieval...")
    
    try:
        bank = Bank()
        
        # Test getting accounts summary
        print("Testing accounts summary retrieval...")
        
        # First check if we have any users
        bank.load_data()
        
        if hasattr(bank, 'users') and bank.users:
            user_id = list(bank.users.keys())[0]
            print(f"Testing with user ID: {user_id}")
            
            accounts_summary = bank.get_accounts_summary(user_id)
            print(f"Found {len(accounts_summary)} accounts")
            
            # Group by bank
            banks = {}
            for account in accounts_summary:
                bank_name = account.get('bank_name', 'Unknown Bank')
                if bank_name not in banks:
                    banks[bank_name] = []
                banks[bank_name].append(account)
            
            print(f"Found {len(banks)} banks:")
            for bank_name, bank_accounts in banks.items():
                total_balance = sum(acc['balance'] for acc in bank_accounts)
                print(f"  {bank_name}: {len(bank_accounts)} accounts, Total: ${total_balance:,.2f}")
                
                # Show account types
                types = {}
                for acc in bank_accounts:
                    acc_type = acc['account_type']
                    if acc_type not in types:
                        types[acc_type] = 0
                    types[acc_type] += 1
                
                for acc_type, count in types.items():
                    print(f"    {acc_type}: {count}")
            
            # Test transaction filtering data
            print("\nTesting transaction data for filtering...")
            transactions = bank.get_user_finances(user_id)
            print(f"Found {len(transactions)} transactions")
            
            if transactions:
                # Show sample transaction structure
                sample_tx = transactions[0]
                print("Sample transaction fields:")
                for key, value in sample_tx.items():
                    print(f"  {key}: {type(value).__name__}")
                
                # Test filtering criteria
                unique_types = set(tx.get('type', 'unknown') for tx in transactions)
                unique_accounts = set(tx.get('account', 'unknown') for tx in transactions)
                unique_categories = set(tx.get('category', 'uncategorized') for tx in transactions)
                
                print(f"\nFilter options:")
                print(f"  Transaction types: {list(unique_types)}")
                print(f"  Accounts: {len(unique_accounts)} unique accounts")
                print(f"  Categories: {len(unique_categories)} unique categories")
        else:
            print("No users found in the system")
            
        print("\n✓ Bank dashboard data test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error testing bank dashboard data: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_financial_tracker_imports():
    """Test that financial tracker can be imported and initialized"""
    print("Testing financial tracker imports...")
    
    try:
        # Test PyQt6 imports
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6 imports successful")
        
        # Test matplotlib imports
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        print("✓ Matplotlib imports successful")
        
        # Test financial tracker import
        sys.path.append(os.path.join(os.path.dirname(__file__), 'ui'))
        from ui.financial_tracker import FinancialTracker
        print("✓ Financial tracker import successful")
        
        print("\n✓ All imports test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Financial Tracker Features Test")
    print("=" * 50)
    
    success = True
    
    # Test imports
    success &= test_financial_tracker_imports()
    print()
    
    # Test data
    success &= test_bank_dashboard_data()
    print()
    
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    print("=" * 50)