#!/usr/bin/env python3
"""
Test script for the enhanced Rent Tracker with notification daemon, due dates, and late fees.

This demonstrates the new features:
1. Due date tracking with customizable monthly due dates
2. Automatic late fee application after grace period
3. Background notification daemon with advance warnings and overdue reminders
4. Configurable notification settings and quiet hours
5. Ability to disable notifications for specific dates
"""

import json
import sys
import os
from datetime import datetime, timedelta

def demonstrate_notification_features():
    print("🔔 Rent Tracker - Enhanced Notification System Demonstration")
    print("=" * 70)
    
    # Load existing test data
    try:
        with open('accounts.json', 'r') as f:
            accounts = json.load(f)
    except FileNotFoundError:
        print("❌ No accounts.json file found. Creating demo data...")
        accounts = {}
    
    # Create demo tenant data with new notification features
    demo_tenant = {
        "rent": 1200.0,
        "due_day": 5,  # Due on the 5th of each month
        "late_fee": {
            "enabled": True,
            "amount": 75.0,
            "grace_period_days": 3
        },
        "disabled_notification_dates": [],
        "payments": [
            {
                "date": "07/05/2025",
                "amount": 1200.0,
                "month": "July",
                "method": "Card"
            }
        ]
    }
    
    accounts["Demo Tenant"] = demo_tenant
    
    # Save demo data
    with open('accounts.json', 'w') as f:
        json.dump(accounts, f, indent=2)
    
    print("\n🏠 NEW FEATURES OVERVIEW:")
    print("-" * 50)
    
    print("""
📅 DUE DATE TRACKING:
• Set custom due day (1-31) for each tenant
• Dashboard shows days until/past due date
• Automatic handling of months with fewer days (e.g., Feb 30 → Feb 28)

💸 LATE FEE AUTOMATION:
• Enable/disable automatic late fees per tenant
• Configurable late fee amount
• Grace period setting (days after due date before fee applies)
• Automatic application as payment entries with "Late Fee" method

🔔 NOTIFICATION DAEMON:
• Background service runs continuously
• Cross-platform notifications (Windows, Mac, Linux)
• Advance warnings (default: 7, 3, 1 days before due)
• Overdue reminders (default: 1, 3, 7, 14 days after due)
• Configurable quiet hours (default: 10 PM - 8 AM)
• Once-per-day notification limit to prevent spam

🚫 NOTIFICATION CONTROL:
• Disable notifications for specific dates
• Calendar interface for easy date selection
• Useful for vacations, holidays, or special circumstances

⚙️ CONFIGURATION OPTIONS:
• Global notification settings (timing, intervals, quiet hours)
• Per-tenant due date and late fee settings
• Easy-to-use GUI dialogs for all settings
""")
    
    print("\n🎯 SAMPLE SCENARIOS:")
    print("-" * 50)
    
    current_date = datetime.now()
    demo_due_day = demo_tenant["due_day"]
    
    # Calculate next due date
    try:
        if current_date.day <= demo_due_day:
            next_due = datetime(current_date.year, current_date.month, demo_due_day)
        else:
            if current_date.month == 12:
                next_due = datetime(current_date.year + 1, 1, demo_due_day)
            else:
                next_due = datetime(current_date.year, current_date.month + 1, demo_due_day)
    except ValueError:
        # Handle months with fewer days
        import calendar
        if current_date.month == 12:
            next_year = current_date.year + 1
            next_month = 1
        else:
            next_year = current_date.year
            next_month = current_date.month + 1
        last_day = calendar.monthrange(next_year, next_month)[1]
        actual_due_day = min(demo_due_day, last_day)
        next_due = datetime(next_year, next_month, actual_due_day)
    
    days_diff = (next_due.date() - current_date.date()).days
    
    print(f"📅 Demo Tenant rent is due on the {demo_due_day}th of each month")
    print(f"📅 Next due date: {next_due.strftime('%B %d, %Y')}")
    
    if days_diff > 0:
        print(f"⏰ Days until due: {days_diff}")
        if days_diff <= 7:
            print("🔔 Notification: Advance warning would be sent")
    elif days_diff == 0:
        print("🚨 Due today! Notification would be sent")
    else:
        print(f"⚠️ {abs(days_diff)} days overdue!")
        print("🔔 Notification: Overdue reminder would be sent")
        
        # Check if late fee would apply
        grace_period = demo_tenant["late_fee"]["grace_period_days"]
        if abs(days_diff) > grace_period:
            late_fee = demo_tenant["late_fee"]["amount"]
            print(f"💸 Late fee would be applied: ${late_fee:.2f}")
    
    print(f"""
📱 TO TEST THE NEW FEATURES:
1. Run: python Rent_Tracker.py
2. Select "Demo Tenant" (or create your own)
3. Click "📅 Due Date & Late Fees" to configure settings
4. Click "🔔 Notification Settings" to adjust timing and quiet hours
5. Click "🚫 Disable Notifications" to block specific dates
6. Watch the dashboard show due date countdown and late fee info
7. Notifications will appear automatically based on your settings

🔧 NOTIFICATION DAEMON:
• Starts automatically when the app launches
• Runs in background even when app is minimized
• Checks every hour for due dates (configurable)
• Respects quiet hours and disabled dates
• Logs all notifications to console for debugging
""")
    
    print("\n✅ TECHNICAL FEATURES:")
    print("• Cross-platform notifications using plyer library")
    print("• Thread-safe daemon with proper cleanup")
    print("• JSON persistence for all new settings")
    print("• Enhanced dashboard with due date countdown")
    print("• Automatic late fee application with audit trail")
    print("• Calendar widget for date selection")
    print("• Comprehensive error handling and validation")

if __name__ == "__main__":
    demonstrate_notification_features()
