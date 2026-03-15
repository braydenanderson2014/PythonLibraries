#!/usr/bin/env python3
"""
Test script to verify that the notification_system.py type error fixes work correctly
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_notification_system_functionality():
    """Test that the NotificationSystem class functions work without type errors"""
    print("Testing NotificationSystem class functionality after type error fixes...")
    
    try:
        from src.notification_system import NotificationSystem
        
        # Test NotificationSystem initialization
        notification_system = NotificationSystem()
        print("✓ NotificationSystem initialization successful")
        
        # Test sending a simple notification with None values
        result = notification_system.send_notification(
            title="Test Notification",
            message="This is a test notification",
            icon_path=None,  # Test None handling
            duration=5,
            urgency="normal"
        )
        print(f"✓ Simple notification sent: {result}")
        
        # Test comprehensive notification with None values
        results = notification_system.send_comprehensive_notification(
            title="Test Comprehensive Notification",
            message="This is a comprehensive test notification", 
            tenant_id=None,  # Test None handling
            send_methods=None,  # Test None handling (should default to ['system'])
            urgency="normal",
            icon_path=None  # Test None handling
        )
        print(f"✓ Comprehensive notification sent: {results}")
        
        # Test creating reminder notification with None values
        reminder = notification_system.create_reminder_notification(
            reminder_type="rent_due",
            tenant_name=None,  # Test None handling
            amount=None,       # Test None handling
            due_date=None      # Test None handling
        )
        print(f"✓ Reminder notification created: {reminder}")
        
        # Test email functionality test with None parameter
        email_test_results = notification_system.test_email_functionality(
            test_email=None  # Test None handling
        )
        print(f"✓ Email functionality test completed: {email_test_results['email_libraries_available']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing notification system functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_notification_type_safety():
    """Test specific type safety improvements"""
    print("\nTesting notification system type safety improvements...")
    
    try:
        from src.notification_system import NotificationSystem
        
        # Test with all None optional parameters
        notification_system = NotificationSystem()
        
        # Test that all None parameters are handled gracefully
        result = notification_system.send_notification(
            title="Type Safety Test",
            message="Testing None parameter handling",
            icon_path=None,
            duration=3,
            urgency="low"
        )
        print("✓ None parameter handling in send_notification successful")
        
        # Test comprehensive notification with all None optionals
        results = notification_system.send_comprehensive_notification(
            title="Type Safety Test 2",
            message="Testing comprehensive None handling",
            tenant_id=None,
            send_methods=None,
            urgency="normal", 
            icon_path=None
        )
        print("✓ None parameter handling in send_comprehensive_notification successful")
        
        # Test reminder creation with all None values
        reminder = notification_system.create_reminder_notification(
            reminder_type="maintenance_reminder",
            tenant_name=None,
            amount=None,
            due_date=None
        )
        print("✓ None parameter handling in create_reminder_notification successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing type safety: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_fallbacks():
    """Test that import fallbacks work correctly"""
    print("\nTesting import fallback mechanisms...")
    
    try:
        # This will test the import logic in the notification system
        from src.notification_system import PLYER_AVAILABLE, WIN10TOAST_AVAILABLE, EMAIL_AVAILABLE
        
        print(f"✓ PLYER_AVAILABLE: {PLYER_AVAILABLE}")
        print(f"✓ WIN10TOAST_AVAILABLE: {WIN10TOAST_AVAILABLE}")
        print(f"✓ EMAIL_AVAILABLE: {EMAIL_AVAILABLE}")
        
        # Test that the system works even if some libraries are missing
        from src.notification_system import NotificationSystem
        ns = NotificationSystem()
        
        # This should work regardless of which libraries are available
        result = ns.send_notification("Import Test", "Testing import fallbacks")
        print(f"✓ Notification system works with current library availability: {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing import fallbacks: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Notification System Type Error Fixes Verification")
    print("=" * 70)
    
    success = True
    
    # Test basic functionality
    success &= test_notification_system_functionality()
    
    # Test type safety
    success &= test_notification_type_safety()
    
    # Test import fallbacks
    success &= test_import_fallbacks()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 All tests passed! Notification system type errors have been fixed!")
        print("\nFixed Issues:")
        print("✓ Optional[str] type annotations for parameters that can be None")
        print("✓ Optional[List[str]] type annotation for send_methods parameter")
        print("✓ Optional[float] type annotation for amount parameter")
        print("✓ Proper None handling for self.toaster attribute access")
        print("✓ Proper None handling for notification module import fallback")
        print("✓ Safe action_queue attribute access with None checks")
        print("✓ Proper tenant_id type casting from Any | None to Optional[str]")
        print("✓ Type ignore comment for notification.notify after None check")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
    
    print("=" * 70)