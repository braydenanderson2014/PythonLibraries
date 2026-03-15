# Rent Tracker - Notification System Documentation

## Overview
The Rent Tracker now includes a comprehensive notification system with automatic due date tracking, late fee management, and configurable alerts. This system runs as a background daemon and provides timely reminders to help manage rental payments effectively.

## Core Features

### 1. Notification Daemon
- **Background Service**: Runs continuously while the application is open
- **Cross-Platform**: Works on Windows, Mac, and Linux using the plyer library
- **Thread-Safe**: Properly managed background thread with cleanup
- **Configurable Intervals**: Check for due dates every 5 minutes to 24 hours
- **Smart Notifications**: Prevents spam by limiting to one notification per scenario per day

### 2. Due Date Management
- **Custom Due Dates**: Set any day of the month (1-31) for each tenant
- **Smart Date Handling**: Automatically adjusts for months with fewer days
- **Dashboard Integration**: Shows countdown and status directly in the main interface
- **Visual Indicators**: 📅 (upcoming), 🚨 (due today), ⚠️ (overdue)

### 3. Late Fee Automation
- **Configurable Per Tenant**: Enable/disable late fees individually
- **Grace Period**: Set days after due date before fees apply (0-14 days)
- **Automatic Application**: Adds late fee as a payment entry automatically
- **Duplicate Prevention**: Only one late fee per month per tenant
- **Audit Trail**: Late fees appear in payment history with "Late Fee" method

### 4. Notification Control
- **Advance Warnings**: Configurable days before due date (e.g., 7, 3, 1 days)
- **Overdue Reminders**: Configurable days after due date (e.g., 1, 3, 7, 14 days)
- **Quiet Hours**: Set time range when no notifications are sent
- **Date Exceptions**: Disable notifications for specific dates (holidays, vacations)

## Configuration Options

### Due Date & Late Fee Settings (Per Tenant)
```
📅 Due Date & Late Fees Button:
- Due Day: 1-31 (day of month rent is due)
- Late Fee Enabled: Enable/disable automatic late fees
- Late Fee Amount: Dollar amount to charge
- Grace Period: Days after due date before fee applies
```

### Notification Settings (Global)
```
🔔 Notification Settings Button:
- Enable Notifications: Master on/off switch
- Check Interval: How often to check for due dates (5-1440 minutes)
- Advance Warnings: Days before due date to warn (comma-separated)
- Overdue Reminders: Days after due date to remind (comma-separated)
- Quiet Hours: Start and end times for no notifications (24-hour format)
```

### Disable Notifications (Per Tenant)
```
🚫 Disable Notifications Button:
- Calendar interface for selecting dates
- Add/remove specific dates when notifications should be blocked
- Useful for holidays, vacations, or special circumstances
```

## Notification Types

### 1. Advance Warnings
- **Trigger**: Configured days before due date
- **Format**: "Rent for [Tenant] is due in X day(s) ([Date])"
- **Purpose**: Give tenants advance notice to prepare payment

### 2. Due Today Alerts
- **Trigger**: On the due date
- **Format**: "Rent for [Tenant] is due TODAY ([Date])"
- **Purpose**: Immediate reminder that payment is due

### 3. Overdue Reminders
- **Trigger**: Configured days after due date
- **Format**: "Rent for [Tenant] is X day(s) overdue (Due: [Date])"
- **Purpose**: Escalating reminders for late payments

### 4. Late Fee Notifications
- **Trigger**: When automatic late fee is applied
- **Format**: "Late fee of $X.XX applied to [Tenant] for [Month]"
- **Purpose**: Inform about automatic late fee application

## Technical Details

### Data Storage
All new settings are stored in the existing `accounts.json` file:

```json
{
  "TenantName": {
    "rent": 1200.0,
    "due_day": 5,
    "late_fee": {
      "enabled": true,
      "amount": 75.0,
      "grace_period_days": 3
    },
    "disabled_notification_dates": [
      "2025-12-25",
      "2025-01-01"
    ],
    "payments": [...]
  }
}
```

### Daemon Configuration
Notification daemon settings are stored in memory and can be configured through the GUI:

```python
notification_settings = {
    'enabled': True,
    'check_interval': 3600,  # seconds
    'advance_warning_days': [7, 3, 1],
    'overdue_reminder_days': [1, 3, 7, 14],
    'quiet_hours_start': 22,  # 10 PM
    'quiet_hours_end': 8,     # 8 AM
}
```

### Thread Management
- **Daemon Thread**: Runs as a daemon thread that automatically cleans up
- **Graceful Shutdown**: Properly stops when application closes
- **Error Handling**: Continues running even if individual notifications fail
- **Resource Management**: Minimal CPU and memory usage

## Usage Examples

### Setting Up a New Tenant with Notifications
1. Create or select a tenant
2. Click "📅 Due Date & Late Fees"
3. Set due day (e.g., 5th of each month)
4. Enable late fees if desired (e.g., $50 after 3-day grace period)
5. Save settings

### Configuring Notification Timing
1. Click "🔔 Notification Settings"
2. Set advance warnings (e.g., "7, 3, 1" for 7, 3, and 1 days before)
3. Set overdue reminders (e.g., "1, 3, 7" for escalating reminders)
4. Configure quiet hours if needed (e.g., 22 to 8 for 10 PM - 8 AM)
5. Save settings

### Disabling Notifications for Holidays
1. Select a tenant
2. Click "🚫 Disable Notifications"
3. Use calendar to select holiday dates
4. Click "Add Selected Date" for each holiday
5. Save changes

## Troubleshooting

### Notifications Not Appearing
- Check if notifications are enabled in "🔔 Notification Settings"
- Verify system notification permissions
- Check if current time is during quiet hours
- Ensure the notification daemon is running (should show in console)

### Late Fees Not Applied
- Verify late fees are enabled for the tenant
- Check if grace period has passed
- Ensure no duplicate late fee exists for the month
- Check console for error messages

### Daemon Not Starting
- Check console for error messages
- Verify plyer library is installed: `pip install plyer`
- Restart the application
- Check system permissions for background processes

## Dependencies
- **plyer**: Cross-platform notification library
- **tkcalendar**: Calendar widget for date selection
- **threading**: Background daemon management
- **datetime**: Date calculations and validation

## Future Enhancements
- Email notifications in addition to system notifications
- SMS integration for critical overdue reminders
- Customizable notification templates
- Integration with calendar applications
- Bulk notification management for multiple tenants
- Notification history and analytics
