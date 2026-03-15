#!/usr/bin/env python3
"""Test script for the enhanced email system."""

from src.notification_system import NotificationSystem

def main():
    print("=== Email System Test ===")
    
    # Create notification system instance
    ns = NotificationSystem()
    
    # Test email status
    print("\n1. Testing Email Setup Status:")
    status = ns.get_email_setup_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Test email functionality
    print("\n2. Testing Email Functionality:")
    test_results = ns.test_email_functionality()
    for key, value in test_results.items():
        print(f"   {key}: {value}")
    
    # Provide configuration instructions
    print("\n3. Configuration Instructions:")
    if not status['ready_to_send']:
        print("   To enable email notifications:")
        print("   - Enable email notifications in settings")
        print("   - Configure your email address")
        print("   - Configure an app password (recommended for Gmail)")
        print("   - Use ns.configure_email('your@email.com', 'your_app_password') to set up")
    else:
        print("   Email system is ready to send notifications!")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
