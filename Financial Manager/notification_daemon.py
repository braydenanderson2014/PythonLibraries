#!/usr/bin/env python3
"""
Notification Daemon for Financial Manager
Can be run as a standalone service to process notification actions
"""

import sys
import os
import time
import signal
import argparse
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.action_queue import ActionQueue
from src.notification_system import NotificationSystem
from assets.Logger import Logger

logger = Logger()

class NotificationDaemon:
    """Standalone notification daemon service"""
    
    def __init__(self, check_interval=60, log_file=None):
        self.check_interval = check_interval
        self.log_file = log_file
        self.running = False
        
        # Initialize components
        self.action_queue = ActionQueue()
        self.notification_system = NotificationSystem(self.action_queue)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def log(self, message):
        """Log message to file and/or console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        logger.debug("NotificationDaemon", log_entry)
        
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry + '\n')
            except Exception as e:
                logger.error("NotificationDaemon", f"Failed to write to log file: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self):
        """Start the daemon"""
        self.running = True
        self.log(f"Notification daemon starting (check interval: {self.check_interval}s)")
        
        # Log system status
        status = self.notification_system.get_daemon_status()
        self.log(f"Notification libraries - Plyer: {status['plyer_available']}, Win10Toast: {status['win10toast_available']}")
        
        try:
            while self.running:
                self.check_and_process_notifications()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.log("Received keyboard interrupt, stopping...")
        except Exception as e:
            self.log(f"Daemon error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the daemon"""
        self.running = False
        self.log("Notification daemon stopped")
    
    def check_and_process_notifications(self):
        """Check for and process due notifications"""
        try:
            # Get current date
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Get due actions
            due_actions = self.action_queue.get_due_actions(current_date)
            
            # Filter for notification actions only
            notification_actions = [
                action for action in due_actions 
                if action['action_type'] == 'notification' and action['status'] == 'pending'
            ]
            
            if notification_actions:
                self.log(f"Found {len(notification_actions)} due notification(s)")
            
            # Process each notification
            for action in notification_actions:
                try:
                    self.process_notification_action(action)
                except Exception as e:
                    self.log(f"Error processing notification {action['action_id']}: {e}")
        
        except Exception as e:
            self.log(f"Error checking for notifications: {e}")
    
    def process_notification_action(self, action):
        """Process a single notification action"""
        action_data = action['action_data']
        
        title = action_data['title']
        message = action_data['message']
        urgency = action_data.get('urgency', 'normal')
        icon_path = action_data.get('icon_path')
        
        self.log(f"Processing notification: {title}")
        
        # Send the notification
        success = self.notification_system.send_notification(
            title=title,
            message=message,
            icon_path=icon_path,
            urgency=urgency
        )
        
        # Mark the action as executed
        execution_result = {
            'title': title,
            'message': message,
            'urgency': urgency,
            'success': success,
            'sent_at': datetime.now().isoformat(),
            'processed_by': 'notification_daemon'
        }
        
        self.action_queue.execute_action(action['action_id'], execution_result)
        
        if success:
            self.log(f"Notification sent successfully: {action['action_id']}")
        else:
            self.log(f"Failed to send notification: {action['action_id']}")
    
    def test_notification(self):
        """Send a test notification"""
        self.log("Sending test notification...")
        success = self.notification_system.send_test_notification()
        if success:
            self.log("Test notification sent successfully")
        else:
            self.log("Test notification failed")
        return success

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Financial Manager Notification Daemon')
    parser.add_argument('--interval', '-i', type=int, default=60,
                       help='Check interval in seconds (default: 60)')
    parser.add_argument('--log', '-l', type=str,
                       help='Log file path (default: console only)')
    parser.add_argument('--test', '-t', action='store_true',
                       help='Send test notification and exit')
    parser.add_argument('--daemon', '-d', action='store_true',
                       help='Run as daemon (default behavior)')
    
    args = parser.parse_args()
    
    # Create daemon instance
    daemon = NotificationDaemon(
        check_interval=args.interval,
        log_file=args.log
    )
    
    if args.test:
        # Just send a test notification and exit
        daemon.log("Running in test mode...")
        success = daemon.test_notification()
        sys.exit(0 if success else 1)
    else:
        # Run the daemon
        daemon.log("Starting Financial Manager Notification Daemon...")
        daemon.log(f"Arguments: interval={args.interval}s, log_file={args.log}")
        daemon.start()

if __name__ == "__main__":
    main()
