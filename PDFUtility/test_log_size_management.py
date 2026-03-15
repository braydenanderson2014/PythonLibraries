#!/usr/bin/env python3
"""
Test to simulate log size management and rotation
"""

import os
from PDFLogger import Logger

def simulate_large_log_test():
    """Simulate what happens when log gets too large"""
    print("📋 Testing log size management...")
    
    try:
        logger = Logger()
        
        print(f"Current log path: {logger.log_file_path}")
        print(f"Max size limit: {logger.max_size_mb} MB")
        
        # Check current size
        current_size = logger.get_current_log_size_mb()
        print(f"Current size: {current_size:.2f} MB")
        
        # Test the size check logic
        if current_size >= logger.max_size_mb:
            print("⚠️ WOULD TRIGGER ROTATION (size >= limit)")
        else:
            print("✅ Size within limits")
        
        # Simulate filling up the log by adding a lot of messages
        print("\n🔄 Testing rotation behavior...")
        for i in range(10):
            logger.info("STRESS_TEST", f"Large log message #{i:04d} - This is a test message to verify that log rotation is working properly when the file gets too large.")
        
        # Force a rotation check
        logger.manually_rotate_if_needed()
        
        new_size = logger.get_current_log_size_mb()
        print(f"Size after test messages: {new_size:.2f} MB")
        
        print("\n✅ Log size management test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simulate_large_log_test()
