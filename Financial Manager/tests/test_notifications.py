#!/usr/bin/env python3
"""
Quick test script for the notification system
"""

import sys
import os
from datetime import datetime, date, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.action_queue import ActionQueue
from src.notification_system import NotificationSystem

def test_notification_system():
    """Test the complete notification system"""
    print("=" * 50)
    print("Financial Manager Notification System Test")
    print("=" * 50)
    
    # Initialize components
    action_queue = ActionQueue()
    notification_system = NotificationSystem(action_queue)
    
    # Test 1: Direct notification
    print("\n1. Testing direct notification...")
    success = notification_system.send_test_notification("normal")
    print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
    
    # Test 2: Queue a notification for today
    print("\n2. Testing notification queuing...")
    try:
        today = date.today().strftime('%Y-%m-%d')
        action_id = notification_system.queue_notification(
            title="Test Queued Notification",
            message="This is a test notification that was queued and should be processed immediately.",
            scheduled_date=today,
            urgency="normal",
            notes="Test queued notification"
        )
        print(f"   Queued with Action ID: {action_id}")
        
        # Check if it's in the queue
        due_actions = action_queue.get_due_actions(today)
        notification_actions = [a for a in due_actions if a['action_type'] == 'notification']
        print(f"   Found {len(notification_actions)} due notification(s)")
        
    except Exception as e:
        print(f"   FAILED: {e}")
    
    # Test 3: Process due notifications
    print("\n3. Testing notification processing...")
    try:
        for action in notification_actions:
            if action['status'] == 'pending':
                notification_system._execute_notification_action(action)
                print(f"   Processed: {action['description']}")
    except Exception as e:
        print(f"   FAILED: {e}")
    
    # Test 4: Template creation
    print("\n4. Testing notification templates...")
    try:
        template = notification_system.create_reminder_notification(
            reminder_type='rent_due',
            tenant_name='John Doe',
            amount=1500.00,
            due_date='2025-10-01'
        )
        print(f"   Template Title: {template['title']}")
        print(f"   Template Message: {template['message']}")
    except Exception as e:
        print(f"   FAILED: {e}")
    
    # Test 5: Daemon status
    print("\n5. Testing daemon status...")
    try:
        status = notification_system.get_daemon_status()
        print(f"   Daemon Running: {status['running']}")
        print(f"   Plyer Available: {status['plyer_available']}")
        print(f"   Win10Toast Available: {status['win10toast_available']}")
    except Exception as e:
        print(f"   FAILED: {e}")
    
    print("\n" + "=" * 50)
    print("Notification system test completed!")
    print("Check your Windows notification area for test notifications.")
    print("=" * 50)

if __name__ == "__main__":
    test_notification_system()
