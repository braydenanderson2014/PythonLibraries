# Tenant Notification System - User Guide

## Overview

The Financial Manager application now includes a comprehensive tenant notification system that integrates with the action queue for automated rent reminders and tenant communications. This system supports multiple delivery methods including system notifications, email, and SMS.

## Key Features

### 1. Enhanced Tenant Contact Information
- **Phone Numbers**: Added separate phone field in tenant creation
- **Email Addresses**: Added separate email field in tenant creation  
- **Backward Compatibility**: Maintains existing contact info structure

### 2. Queue Control Center
- **Manual Queue Management**: Add, view, and remove scheduled actions
- **Multiple Action Types**: Support for notifications, rent changes, lease renewals
- **Flexible Scheduling**: Schedule actions for future dates
- **Multiple Send Methods**: Choose system, email, and/or SMS delivery

### 3. Enhanced Notification System
- **Multi-Channel Delivery**: Send via system notifications, email, and SMS
- **Tenant-Specific Contact**: Automatically uses tenant contact information
- **Template Support**: Predefined templates for common notifications
- **Queue Integration**: Seamless integration with action queue system

## How to Use

### Accessing the System

1. **Login as Admin**: The notification features require admin privileges
2. **Access Queue Control**: Go to Admin menu → "Queue Control Center"
3. **Access Notification Manager**: Go to Admin menu → "Notification Manager"

### Adding Tenant Contact Information

When creating a new tenant:
1. Fill in the **Phone** field with format: (555) 123-4567
2. Fill in the **Email** field with a valid email address
3. These fields enable email and SMS notifications for that tenant

### Using Queue Control Center

#### Add to Queue Tab:
1. **Select Tenant**: Choose the tenant to send notification to
2. **Choose Action Type**: Select "notification" for sending messages
3. **Set Scheduled Date**: Choose when to send the notification
4. **Configure Details**:
   - **Notification Type**: rent_due, lease_expiry, payment_overdue, etc.
   - **Message**: Enter your notification message
   - **Urgency**: normal, low, or critical
   - **Send Via**: Check email, SMS, and/or system notification

5. **Click "Add to Queue"**: The notification will be scheduled

#### View Queue Tab:
- **See All Actions**: View all scheduled actions in the system
- **Monitor Status**: See pending, completed, or failed actions
- **Remove Actions**: Delete unwanted scheduled actions

### Using Notification Manager

#### Quick Templates:
1. **Select Template**: Choose from predefined templates like "Rent Due Reminder"
2. **Select Tenant**: Choose the tenant to notify
3. **Enter Amount**: For payment-related templates
4. **Send Now or Schedule**: Choose immediate or future delivery

#### Manual Notifications:
1. **Enter Title**: Notification title (e.g., "Rent Reminder")
2. **Enter Message**: Detailed message content
3. **Select Tenant**: Choose tenant (optional for system-wide notifications)
4. **Choose Send Methods**: 
   - ☑ System Notification (Windows toast)
   - ☐ Email (requires tenant email address)
   - ☐ SMS (requires tenant phone number)
5. **Set Schedule**: Choose when to send
6. **Click "Queue Notification"**

### Automatic Rent Reminders

The system can automatically schedule rent reminders:

1. **Go to Queue Control Center**
2. **Add Notification Action**:
   - **Tenant**: Select the tenant
   - **Scheduled Date**: Set to a few days before rent due date
   - **Notification Type**: "rent_due"
   - **Message**: "Your rent payment of $[amount] is due on [date]"
   - **Send Via**: Enable email and/or SMS for better reach

3. **Recurring Setup**: For recurring reminders, manually add actions for future months

## Send Method Details

### System Notifications
- **Windows Toast**: Pop-up notifications on Windows desktop
- **Always Available**: Works on any Windows system
- **Immediate**: Delivered instantly when due

### Email Notifications  
- **Requires Configuration**: Email server settings needed
- **Tenant Email Required**: Tenant must have email address
- **Professional Format**: Formatted email with title and message

### SMS Notifications
- **Placeholder Implementation**: Currently simulated (prints to console)
- **Future Integration**: Designed for Twilio, AWS SNS integration
- **Tenant Phone Required**: Tenant must have phone number

## Configuration

### Email Setup (Optional)
1. **Edit settings.json**: Add email configuration:
```json
{
  "email_notifications": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email": "your-email@gmail.com",
    "password": "your-app-password"
  }
}
```

### SMS Setup (Future)
1. **Service Integration**: Connect with Twilio or similar service
2. **Configuration**: Add SMS provider credentials to settings
3. **Phone Validation**: Ensure tenant phone numbers are properly formatted

## Best Practices

### Scheduling Rent Reminders
1. **Advance Notice**: Schedule 3-5 days before rent due date
2. **Multiple Channels**: Use both email and system notifications
3. **Clear Messages**: Include amount, due date, and payment instructions

### Contact Information Management
1. **Verify Information**: Ensure email and phone numbers are accurate
2. **Update Regularly**: Keep tenant contact info current
3. **Privacy Consideration**: Secure storage of contact information

### Queue Management
1. **Regular Review**: Check the queue for pending actions
2. **Remove Old Actions**: Clean up completed or unnecessary actions
3. **Monitor Failures**: Address failed notification attempts

## Troubleshooting

### Common Issues

#### "No email address for tenant"
- **Solution**: Add email address in tenant contact information
- **Workaround**: Use system notifications only

#### "Email libraries not available"
- **Cause**: Python environment missing email modules
- **Solution**: Install required packages or use system notifications

#### "SMS not configured"
- **Expected**: SMS is currently simulated
- **Solution**: Use email and system notifications

### Verification Steps

1. **Test System Notifications**: Use "Test Notification" button
2. **Check Queue Status**: View actions in Queue Control Center
3. **Verify Tenant Info**: Confirm contact information is complete
4. **Monitor Console**: Check terminal output for error messages

## Integration with Existing Features

### Monthly Balance Summaries
- Queue status shows in monthly balance view
- Scheduled actions appear with relevant months

### Tenant Management
- Contact info integrates with existing tenant system
- Maintains backward compatibility

### Action Queue System
- All notifications use the existing queue infrastructure
- Same processing and execution system

## Security Considerations

### Email Configuration
- **App Passwords**: Use app-specific passwords, not account passwords
- **Secure Storage**: Store credentials securely
- **Access Control**: Admin-only access to configuration

### Tenant Privacy
- **Contact Information**: Protect tenant contact details
- **Notification Content**: Avoid sensitive information in messages
- **Access Logs**: Monitor notification sending activity

---

## Quick Start Checklist

- [ ] Login as admin user
- [ ] Add tenant contact information (phone/email)
- [ ] Test system notifications via Notification Manager
- [ ] Schedule a sample notification via Queue Control Center
- [ ] Verify notification appears in queue
- [ ] Monitor execution at scheduled time

For additional support or feature requests, check the application logs or contact the development team.
