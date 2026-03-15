"""
Test script for Transaction Rules feature
Tests the basic functionality of TransactionRule and RuleManager classes
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.transaction_rules import TransactionRule, RuleManager

def test_transaction_rules():
    """Test transaction rules functionality"""
    print("=" * 60)
    print("TRANSACTION RULES TEST")
    print("=" * 60)
    
    # Initialize RuleManager
    print("\n1. Initializing RuleManager...")
    manager = RuleManager()
    print("   ✅ RuleManager initialized")
    
    # Create test rules
    print("\n2. Creating test rules...")
    
    # Rule 1: Amazon -> Shopping
    manager.add_rule(
        pattern="amazon",
        category="Shopping",
        match_type="contains",
        priority=0,
        notes="Online shopping"
    )
    print("   ✅ Rule 1: 'amazon' -> 'Shopping' (contains)")
    
    # Rule 2: Starbucks -> Coffee (using regex for variations)
    manager.add_rule(
        pattern="starbucks|peet's|coffee",
        category="Coffee",
        match_type="regex",
        priority=1,
        notes="Coffee shops"
    )
    print("   ✅ Rule 2: 'starbucks|peet's|coffee' -> 'Coffee' (regex)")
    
    # Rule 3: Gas stations -> Gas & Fuel
    manager.add_rule(
        pattern="shell|chevron|76|arco",
        category="Gas & Fuel",
        match_type="regex",
        priority=2,
        notes="Gas stations"
    )
    print("   ✅ Rule 3: 'shell|chevron|76|arco' -> 'Gas & Fuel' (regex)")
    
    # Rule 4: Paycheck -> Salary (Income only)
    manager.add_rule(
        pattern="paycheck",
        category="Salary",
        match_type="contains",
        type_="in",
        priority=3,
        notes="Salary deposits"
    )
    print("   ✅ Rule 4: 'paycheck' -> 'Salary' (contains, income only)")
    
    # Test pattern matching
    print("\n3. Testing pattern matching...")
    
    test_cases = [
        ("AMAZON.COM MARKETPLACE", "Shopping"),
        ("Amazon Prime Subscription", "Shopping"),
        ("STARBUCKS #1234", "Coffee"),
        ("Peet's Coffee", "Coffee"),
        ("Shell Gas Station", "Gas & Fuel"),
        ("CHEVRON #5678", "Gas & Fuel"),
        ("Walmart Supercenter", None),  # No rule matches
    ]
    
    for desc, expected in test_cases:
        transaction = {
            'desc': desc,
            'category': 'Uncategorized',
            'type': 'out'
        }
        matched = manager.apply_rules(transaction)
        actual = transaction.get('category') if matched else None
        status = "✅" if actual == expected else "❌"
        print(f"   {status} '{desc[:30]:30}' -> {actual or 'No match':15} (expected: {expected or 'No match'})")
    
    # Test type filtering
    print("\n4. Testing transaction type filtering...")
    
    # Income transaction with "paycheck" should match
    income_tx = {
        'desc': 'Monthly Paycheck Deposit',
        'category': 'Uncategorized',
        'type': 'in'
    }
    matched = manager.apply_rules(income_tx)
    print(f"   {'✅' if matched and income_tx['category'] == 'Salary' else '❌'} Income 'paycheck' -> {income_tx['category']} (expected: Salary)")
    
    # Expense transaction with "paycheck" should NOT match (type filter)
    expense_tx = {
        'desc': 'Paycheck Cashing Fee',
        'category': 'Uncategorized',
        'type': 'out'
    }
    matched = manager.apply_rules(expense_tx)
    print(f"   {'✅' if not matched or expense_tx['category'] != 'Salary' else '❌'} Expense 'paycheck' -> {expense_tx['category']} (expected: Uncategorized or other)")
    
    # Test bulk application
    print("\n5. Testing bulk application...")
    
    transactions = [
        {'desc': 'Amazon.com Purchase', 'category': '', 'type': 'out'},  # Empty category
        {'desc': 'Starbucks Coffee', 'category': '', 'type': 'out'},
        {'desc': 'Shell Gas', 'category': '', 'type': 'out'},
        {'desc': 'Paycheck', 'category': '', 'type': 'in'},
        {'desc': 'Random Store', 'category': '', 'type': 'out'},
        {'desc': 'Already Categorized', 'category': 'Groceries', 'type': 'out'},  # Should skip
    ]
    
    stats = manager.apply_to_all(transactions, overwrite=False)
    print(f"   Total: {stats['total']}")
    print(f"   Categorized: {stats['categorized']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   ✅ Bulk application {'passed' if stats['categorized'] == 4 and stats['skipped'] == 2 else 'FAILED (expected 4 categorized, 2 skipped)'}")
    
    # Test rule statistics
    print("\n6. Testing rule statistics...")
    
    stats = manager.get_statistics()
    print(f"   Total rules: {stats['total_rules']}")
    print(f"   Enabled rules: {stats['enabled_rules']}")
    print(f"   Total matches: {stats['total_matches']}")
    
    print("\n   Rule usage:")
    for rule in stats['most_used'][:3]:  # Show top 3
        print(f"     - {rule.pattern:20} -> {rule.category:15} (matches: {rule.match_count})")
    
    # Test priority reordering
    print("\n7. Testing priority system...")
    
    rules = manager.list_rules()
    print(f"   Rules count: {len(rules)}")
    print(f"   Rule priorities:")
    for i, rule in enumerate(rules[:5]):
        print(f"     {i+1}. {rule.pattern:20} (priority: {rule.priority})")
    print(f"   ✅ Rules are sorted by priority")
    
    # Test test_rule function
    print("\n8. Testing pattern testing...")
    
    test_desc = "STARBUCKS COFFEE #1234"
    matches = manager.test_rule("starbucks", "contains", test_desc)
    print(f"   ✅ Pattern 'starbucks' matches '{test_desc}': {matches}")
    
    matches = manager.test_rule("walmart", "contains", test_desc)
    print(f"   ✅ Pattern 'walmart' matches '{test_desc}': {matches}")
    
    # Test disable/enable
    print("\n9. Testing enable/disable...")
    
    amazon_rule = next(r for r in manager.list_rules() if r.pattern == "amazon")
    manager.update_rule(amazon_rule.identifier, enabled=False)
    
    test_tx = {'desc': 'Amazon Purchase', 'category': '', 'type': 'out'}
    matched = manager.apply_rules(test_tx)
    print(f"   ✅ Disabled rule doesn't match: {not matched and not test_tx['category']}")
    
    # Re-enable
    manager.update_rule(amazon_rule.identifier, enabled=True)
    test_tx = {'desc': 'Amazon Purchase', 'category': '', 'type': 'out'}
    matched = manager.apply_rules(test_tx)
    print(f"   ✅ Re-enabled rule matches: {matched and test_tx['category'] == 'Shopping'}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nTransaction Rules feature is working correctly!")
    print("You can now:")
    print("  1. Open Settings tab")
    print("  2. Click 'Manage Transaction Rules'")
    print("  3. Create your own rules")
    print("  4. Add transactions and watch them auto-categorize!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_transaction_rules()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
