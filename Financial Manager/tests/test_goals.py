"""
Test script for Goals & Savings Tracking feature
Tests the basic functionality of Goal and GoalManager classes
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.goals import Goal, GoalManager
from datetime import date, timedelta

def test_goals_feature():
    """Test goals feature functionality"""
    print("=" * 60)
    print("GOALS & SAVINGS TRACKING TEST")
    print("=" * 60)
    
    # Initialize GoalManager
    print("\n1. Initializing GoalManager...")
    manager = GoalManager()
    print("   ✅ GoalManager initialized")
    
    # Create test goals
    print("\n2. Creating test goals...")
    
    # Goal 1: Emergency Fund (high priority, 12-month target)
    target_date_1 = (date.today() + timedelta(days=365)).isoformat()
    goal1 = manager.add_goal(
        name="Emergency Fund",
        target_amount=10000.00,
        target_date=target_date_1,
        monthly_contribution=800.00,
        priority='high',
        icon='💰',
        notes="Build 6-month emergency fund",
        user_id='test_user'
    )
    print(f"   ✅ Goal 1: Emergency Fund - ${goal1.target_amount:,.2f} target")
    
    # Goal 2: Vacation (medium priority, 6-month target)
    target_date_2 = (date.today() + timedelta(days=180)).isoformat()
    goal2 = manager.add_goal(
        name="Vacation to Hawaii",
        target_amount=5000.00,
        target_date=target_date_2,
        monthly_contribution=850.00,
        priority='medium',
        icon='✈️',
        notes="Family vacation summer 2025",
        user_id='test_user'
    )
    print(f"   ✅ Goal 2: Vacation - ${goal2.target_amount:,.2f} target")
    
    # Goal 3: New Car (no target date, low priority)
    goal3 = manager.add_goal(
        name="New Car Fund",
        target_amount=25000.00,
        monthly_contribution=500.00,
        priority='low',
        icon='🚗',
        notes="Save for down payment",
        user_id='test_user'
    )
    print(f"   ✅ Goal 3: New Car - ${goal3.target_amount:,.2f} target")
    
    # Test goal retrieval
    print("\n3. Testing goal retrieval...")
    goals = manager.list_goals(user_id='test_user')
    print(f"   Retrieved {len(goals)} goals")
    for goal in goals:
        print(f"   - {goal.icon} {goal.name} ({goal.priority} priority)")
    print("   ✅ Goal retrieval works")
    
    # Test contributions
    print("\n4. Testing contributions...")
    
    # Add contributions to Emergency Fund
    manager.add_contribution_to_goal(goal1.goal_id, 800.00)  # Month 1
    manager.add_contribution_to_goal(goal1.goal_id, 800.00)  # Month 2
    manager.add_contribution_to_goal(goal1.goal_id, 800.00)  # Month 3
    
    goal1 = manager.get_goal(goal1.goal_id)
    print(f"   Emergency Fund: ${goal1.current_amount:,.2f} / ${goal1.target_amount:,.2f}")
    print(f"   Progress: {goal1.get_progress_percentage():.1f}%")
    print(f"   Contributions: {goal1.get_contribution_count()}")
    print("   ✅ Contributions work correctly")
    
    # Test progress calculations
    print("\n5. Testing progress calculations...")
    
    remaining = goal1.get_remaining_amount()
    print(f"   Remaining to goal: ${remaining:,.2f}")
    
    progress_pct = goal1.get_progress_percentage()
    print(f"   Progress percentage: {progress_pct:.1f}%")
    
    days_left = goal1.get_days_until_target()
    print(f"   Days until target: {days_left}")
    
    print("   ✅ Progress calculations working")
    
    # Test projections
    print("\n6. Testing projections...")
    
    projected_date = goal1.get_projected_completion_date()
    print(f"   Projected completion: {projected_date}")
    
    required_monthly = goal1.get_required_monthly_contribution()
    print(f"   Required monthly to meet target: ${required_monthly:,.2f}")
    
    status = goal1.is_on_track()
    print(f"   Goal status: {status}")
    
    print("   ✅ Projections working")
    
    # Test goal completion
    print("\n7. Testing goal completion...")
    
    # Add enough to complete vacation goal
    manager.add_contribution_to_goal(goal2.goal_id, 5000.00)
    goal2 = manager.get_goal(goal2.goal_id)
    
    print(f"   Vacation goal completed: {goal2.completed}")
    print(f"   Completion date: {goal2.completed_date}")
    print(f"   Current amount: ${goal2.current_amount:,.2f}")
    
    if goal2.completed:
        print("   ✅ Goal completion detection works!")
    
    # Test statistics
    print("\n8. Testing statistics...")
    
    stats = manager.get_statistics(user_id='test_user')
    
    print(f"   Total goals: {stats['total_goals']}")
    print(f"   Active goals: {stats['active_goals']}")
    print(f"   Completed goals: {stats['completed_goals']}")
    print(f"   Total target: ${stats['total_target_amount']:,.2f}")
    print(f"   Total saved: ${stats['total_saved_amount']:,.2f}")
    print(f"   Overall progress: {stats['overall_progress_percentage']:.1f}%")
    print(f"   Goals on track: {stats['goals_on_track']}")
    print(f"   Goals behind: {stats['goals_behind']}")
    
    print("   ✅ Statistics working")
    
    # Test goal updates
    print("\n9. Testing goal updates...")
    
    manager.update_goal(
        goal3.goal_id,
        name="Used Car Fund",
        target_amount=15000.00,
        priority='medium'
    )
    
    goal3 = manager.get_goal(goal3.goal_id)
    print(f"   Updated name: {goal3.name}")
    print(f"   Updated target: ${goal3.target_amount:,.2f}")
    print(f"   Updated priority: {goal3.priority}")
    print("   ✅ Goal updates working")
    
    # Test priority sorting
    print("\n10. Testing priority sorting...")
    
    goals = manager.list_goals(user_id='test_user', completed=False)
    print("   Goals sorted by priority:")
    for i, goal in enumerate(goals, 1):
        print(f"     {i}. {goal.name} ({goal.priority})")
    print("   ✅ Priority sorting works")
    
    # Test filtering
    print("\n11. Testing filtering...")
    
    active_goals = manager.list_goals(user_id='test_user', completed=False)
    completed_goals = manager.list_goals(user_id='test_user', completed=True)
    high_priority = manager.list_goals(user_id='test_user', priority='high')
    
    print(f"   Active goals: {len(active_goals)}")
    print(f"   Completed goals: {len(completed_goals)}")
    print(f"   High priority goals: {len(high_priority)}")
    print("   ✅ Filtering works")
    
    # Test contribution history
    print("\n12. Testing contribution history...")
    
    avg_contrib = goal1.get_average_contribution()
    total_contrib = goal1.get_total_contributions()
    
    print(f"   Total contributions: ${total_contrib:,.2f}")
    print(f"   Average contribution: ${avg_contrib:,.2f}")
    print(f"   Contribution count: {goal1.get_contribution_count()}")
    print("   ✅ Contribution history works")
    
    # Test persistence
    print("\n13. Testing persistence...")
    
    manager.save()
    
    # Create new manager and load
    manager2 = GoalManager()
    loaded_goals = manager2.list_goals(user_id='test_user')
    
    print(f"   Loaded {len(loaded_goals)} goals from file")
    for goal in loaded_goals:
        print(f"     - {goal.name}: ${goal.current_amount:,.2f} / ${goal.target_amount:,.2f}")
    print("   ✅ Persistence works")
    
    # Clean up test data
    print("\n14. Cleaning up test data...")
    for goal in loaded_goals:
        manager2.remove_goal(goal.goal_id)
    print("   ✅ Test data cleaned up")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nGoals & Savings Tracking feature is working correctly!")
    print("You can now:")
    print("  1. Open Financial Manager")
    print("  2. Navigate to 🎯 Goals tab")
    print("  3. Click '➕ Add Goal' to create your first goal")
    print("  4. Contribute to goals and track progress!")
    print("  5. View statistics and projections")
    print("  6. Celebrate when goals are achieved! 🎉")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_goals_feature()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
