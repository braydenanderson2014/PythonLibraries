#!/usr/bin/env python3
"""
Test script for the Budget System
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.budget import Budget, BudgetManager
from datetime import datetime

def test_budget_creation():
    """Test creating a budget"""
    print("Testing Budget Creation...")
    budget = Budget(
        category="Groceries",
        monthly_limit=500.00,
        user_id="test_user"
    )
    assert budget.category == "Groceries"
    assert budget.monthly_limit == 500.00
    print("✓ Budget creation successful")

def test_budget_manager():
    """Test budget manager functionality"""
    print("\nTesting Budget Manager...")
    
    # Create manager
    manager = BudgetManager(user_id="test_user")
    
    # Add a budget
    budget = Budget(
        category="Test Category",
        monthly_limit=300.00,
        user_id="test_user"
    )
    manager.add_budget(budget)
    print(f"✓ Added budget: {budget.category}")
    
    # Get budget
    retrieved = manager.get_budget("Test Category")
    assert retrieved is not None
    assert retrieved.category == "Test Category"
    print("✓ Retrieved budget successfully")
    
    # Test budget status calculation
    sample_transactions = [
        {
            'amount': 50.00,
            'category': 'Test Category',
            'type': 'out',
            'date': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'amount': 100.00,
            'category': 'Test Category',
            'type': 'out',
            'date': datetime.now().strftime('%Y-%m-%d')
        }
    ]
    
    status = manager.get_budget_status(sample_transactions, "Test Category")
    print(f"✓ Budget status: Spent ${status['spent']:.2f} of ${budget.monthly_limit:.2f}")
    print(f"  Status: {status['status']} (Color: {status['color']})")
    assert status['spent'] == 150.00
    assert status['status'] == 'good'
    
    # Test transaction checking
    new_transaction = {
        'amount': 200.00,
        'category': 'Test Category',
        'type': 'out',
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    
    check_result = manager.check_transaction(new_transaction, sample_transactions)
    print(f"✓ Transaction check: {check_result['message']}")
    
    # Clean up
    manager.remove_budget(budget.identifier)
    print("✓ Removed test budget")

def test_budget_colors():
    """Test budget color logic"""
    print("\nTesting Budget Color Logic...")
    
    manager = BudgetManager(user_id="test_user")
    budget = Budget(
        category="Color Test",
        monthly_limit=100.00,
        user_id="test_user",
        warning_threshold=0.8
    )
    manager.add_budget(budget)
    
    # Test good status (under 80%)
    transactions_good = [
        {'amount': 50.00, 'category': 'Color Test', 'type': 'out', 'date': datetime.now().strftime('%Y-%m-%d')}
    ]
    status = manager.get_budget_status(transactions_good, "Color Test")
    assert status['status'] == 'good'
    assert status['color'] == '#4CAF50'
    print(f"✓ Good status (50%): {status['color']}")
    
    # Test warning status (80-100%)
    transactions_warning = [
        {'amount': 85.00, 'category': 'Color Test', 'type': 'out', 'date': datetime.now().strftime('%Y-%m-%d')}
    ]
    status = manager.get_budget_status(transactions_warning, "Color Test")
    assert status['status'] == 'warning'
    assert status['color'] == '#FF9800'
    print(f"✓ Warning status (85%): {status['color']}")
    
    # Test over status (>100%)
    transactions_over = [
        {'amount': 120.00, 'category': 'Color Test', 'type': 'out', 'date': datetime.now().strftime('%Y-%m-%d')}
    ]
    status = manager.get_budget_status(transactions_over, "Color Test")
    assert status['status'] == 'over'
    assert status['color'] == '#F44336'
    print(f"✓ Over status (120%): {status['color']}")
    
    # Clean up
    manager.remove_budget(budget.identifier)
    print("✓ Cleaned up test budget")

if __name__ == '__main__':
    print("="*50)
    print("Budget System Test Suite")
    print("="*50)
    
    try:
        test_budget_creation()
        test_budget_manager()
        test_budget_colors()
        
        print("\n" + "="*50)
        print("✓ All tests passed!")
        print("="*50)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
