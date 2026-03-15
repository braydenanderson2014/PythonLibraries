#!/usr/bin/env python3
"""Test script to configure and test the email system."""

from src.notification_system import NotificationSystem

def main():
    print("=== Email Configuration Test ===")
    
    # Create notification system instance
    ns = NotificationSystem()
    
    # Enable email notifications first
    print("\n1. Enabling email notifications...")
    ns.enable_email_notifications()
    
    # Check status after enabling
    print("\n2. Email Setup Status After Enabling:")
    status = ns.get_email_setup_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Test SMTP connection (should fail without credentials but show the capability)
    print("\n3. Testing SMTP Connection (without credentials):")
    test_results = ns.test_email_functionality()
    for key, value in test_results.items():
        print(f"   {key}: {value}")
    
    print("\n4. Configuration Example:")
    print("   To fully configure email:")
    print("   ns.configure_email('your@gmail.com', 'your_app_password')")
    print("   This will set up email and password for sending notifications.")
    
    print("\n=== Configuration Test Complete ===")

if __name__ == "__main__":
    main()
