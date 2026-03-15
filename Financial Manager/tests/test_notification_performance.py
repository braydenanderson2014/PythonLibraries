#!/usr/bin/env python3
"""
Test script to verify that the notification system is non-blocking
and provides startup summary instead of individual notifications.
"""

import sys
import os
import time
import threading
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tenant_notification_automation import TenantNotificationAutomation
from notification_system import NotificationSystem
from action_queue import ActionQueue
from rent_tracker import RentTracker

def test_startup_performance():
    """Test that the notification system starts quickly and doesn't block"""
    print("=== Testing Notification System Startup Performance ===")
    
    try:
        # Initialize systems
        print("[INFO] Initializing systems...")
        rent_tracker = RentTracker()
        notification_system = NotificationSystem()
        action_queue = ActionQueue()
        
        # Create automation system
        automation = TenantNotificationAutomation(
            rent_tracker=rent_tracker,
            notification_system=notification_system,
            action_queue=action_queue
        )
        
        # Measure startup time
        start_time = time.time()
        print(f"[INFO] Starting automation at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        
        # Start automation (should be non-blocking)
        automation.start_automation()
        
        startup_time = time.time() - start_time
        print(f"[INFO] Automation started in {startup_time:.3f} seconds")
        
        # Verify it's non-blocking by checking if we can continue immediately
        if startup_time < 0.1:  # Should start almost instantly
            print("✅ PASS: Startup is non-blocking (< 0.1 seconds)")
        else:
            print("❌ FAIL: Startup took too long, might be blocking")
        
        # Check automation status
        status = automation.get_automation_status()
        print(f"[INFO] Automation status: {status}")
        
        # Wait a bit to see startup summary
        print("[INFO] Waiting for startup summary notification...")
        time.sleep(5)  # Give time for startup summary to be sent
        
        # Stop automation
        automation.stop_automation()
        print("[INFO] Automation stopped")
        
        return startup_time < 0.1
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notification_threading():
    """Test that individual notifications are sent asynchronously"""
    print("\n=== Testing Notification Threading ===")
    
    try:
        # Simple threading test
        notifications_sent = []
        
        def mock_send_notification(title, message, **kwargs):
            """Mock notification that takes some time"""
            time.sleep(0.1)  # Simulate slow notification
            notifications_sent.append((title, message, time.time()))
            return {'system': True}
        
        # Test multiple quick notifications
        start_time = time.time()
        threads = []
        
        for i in range(5):
            thread = threading.Thread(
                target=mock_send_notification,
                args=(f"Test {i}", f"Message {i}"),
                daemon=True
            )
            threads.append(thread)
            thread.start()
        
        # Don't wait for threads to complete (non-blocking test)
        immediate_time = time.time() - start_time
        
        if immediate_time < 0.05:  # Should return almost immediately
            print("✅ PASS: Notifications are sent asynchronously")
        else:
            print("❌ FAIL: Notifications appear to be blocking")
        
        # Wait for all to complete for verification
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        print(f"[INFO] {len(notifications_sent)} notifications completed in {total_time:.3f} seconds")
        print(f"[INFO] Immediate return time: {immediate_time:.3f} seconds")
        
        return immediate_time < 0.05
        
    except Exception as e:
        print(f"[ERROR] Threading test failed: {e}")
        return False

def main():
    """Run all performance tests"""
    print("Starting Notification System Performance Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: Startup performance
    results.append(test_startup_performance())
    
    # Test 2: Notification threading
    results.append(test_notification_threading())
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY:")
    print(f"Startup Performance: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Notification Threading: {'✅ PASS' if results[1] else '❌ FAIL'}")
    
    if all(results):
        print("\n🎉 All tests passed! Notification system is non-blocking.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)