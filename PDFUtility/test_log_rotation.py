#!/usr/bin/env python3
"""
Test script to verify log rotation functionality
"""

import os
import time
from PDFLogger import Logger

def test_log_rotation():
    """Test the enhanced logging system with rotation"""
    print("🔧 Testing enhanced logging with rotation...")
    
    try:
        # Initialize logger
        logger = Logger()
        
        # Get current log file info
        log_path = logger.log_file_path
        print(f"✅ Log file path: {log_path}")
        print(f"✅ Max size setting: {logger.max_size_mb} MB")
        print(f"✅ Backup count: {logger.backup_count}")
        
        # Check if log file exists and get current size
        if os.path.exists(log_path):
            current_size = logger.get_current_log_size_mb()
            print(f"✅ Current log file size: {current_size:.2f} MB")
            
            # Check if rotation is needed
            if current_size >= logger.max_size_mb:
                print(f"⚠️  Log file ({current_size:.2f} MB) exceeds limit ({logger.max_size_mb} MB)")
                print("🔄 Attempting manual rotation...")
                logger.manually_rotate_if_needed()
                
                # Check size after rotation
                new_size = logger.get_current_log_size_mb()
                print(f"✅ Log file size after rotation: {new_size:.2f} MB")
            else:
                print(f"✅ Log file size is within limit")
        else:
            print("ℹ️  No existing log file found - will be created on first log")
        
        # Test logging with size info
        logger.info("TEST", "Testing enhanced logging system with rotation")
        logger.info("SETTINGS", f"Log rotation configured: {logger.max_size_mb}MB max, {logger.backup_count} backups")
        
        # Check for backup files
        log_dir = os.path.dirname(log_path)
        log_filename = os.path.basename(log_path)
        backup_files = []
        
        for i in range(1, logger.backup_count + 1):
            backup_file = os.path.join(log_dir, f"{log_filename}.{i}")
            if os.path.exists(backup_file):
                backup_size = os.path.getsize(backup_file) / (1024 * 1024)
                backup_files.append(f"{backup_file} ({backup_size:.2f} MB)")
        
        if backup_files:
            print(f"✅ Found {len(backup_files)} backup file(s):")
            for backup in backup_files:
                print(f"   📄 {backup}")
        else:
            print("ℹ️  No backup files found")
        
        print("\n🎉 Log rotation test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_log_rotation()
