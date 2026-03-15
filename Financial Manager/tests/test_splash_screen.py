"""
Quick Test Script for Splash Screen
Run this to see the splash screen in action without integrating it into the main app.

Usage:
    python test_splash_screen.py
"""

import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add parent directory to path for imports
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets.SplashScreen import SplashScreen


def test_basic_splash():
    """Test basic splash screen with simulated loading"""
    print("=" * 60)
    print("SPLASH SCREEN TEST - Basic Mode")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # Create splash with all features enabled
    splash = SplashScreen(
        image_path=None,  # Uses default gradient
        show_percentage=True,
        show_message=True,
        app_name="Financial Manager",
        version="1.0.0",
        width=600,
        height=400
    )
    
    splash.show()
    print("✓ Splash screen created and shown")
    
    # Simulate loading process
    loading_steps = [
        (0, "Initializing application..."),
        (10, "Loading configuration files..."),
        (20, "Connecting to database..."),
        (35, "Loading user preferences..."),
        (50, "Initializing modules..."),
        (65, "Loading financial data..."),
        (75, "Setting up stock tracker..."),
        (85, "Building user interface..."),
        (95, "Finalizing setup..."),
        (100, "Ready to launch!")
    ]
    
    def simulate_loading():
        for i, (progress, message) in enumerate(loading_steps):
            print(f"  [{progress:3d}%] {message}")
            splash.set_progress(progress, message)
            time.sleep(0.5)  # Simulate work being done
            QApplication.processEvents()
        
        # Keep splash visible for a moment
        print("\n✓ Loading complete! Closing splash screen...")
        time.sleep(1)
        splash.close()
        
        print("✓ Test completed successfully!")
        print("=" * 60)
        app.quit()
    
    # Start simulation after a brief delay
    QTimer.singleShot(500, simulate_loading)
    
    sys.exit(app.exec())


def test_minimal_splash():
    """Test minimal splash screen (no percentage, no message)"""
    print("=" * 60)
    print("SPLASH SCREEN TEST - Minimal Mode")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    splash = SplashScreen(
        show_percentage=False,
        show_message=False,
        app_name="Financial Manager",
        version="1.0.0"
    )
    
    splash.show()
    print("✓ Minimal splash screen shown")
    
    def simulate_loading():
        for progress in range(0, 101, 10):
            splash.set_progress(progress)
            time.sleep(0.3)
            QApplication.processEvents()
        
        print("✓ Loading complete!")
        time.sleep(0.5)
        splash.close()
        app.quit()
    
    QTimer.singleShot(500, simulate_loading)
    sys.exit(app.exec())


def test_percentage_only():
    """Test splash with percentage only (no messages)"""
    print("=" * 60)
    print("SPLASH SCREEN TEST - Percentage Only Mode")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    splash = SplashScreen(
        show_percentage=True,
        show_message=False,
        app_name="Financial Manager",
        version="1.0.0"
    )
    
    splash.show()
    print("✓ Percentage-only splash screen shown")
    
    def simulate_loading():
        for progress in range(0, 101, 5):
            splash.set_progress(progress)
            print(f"  Progress: {progress}%")
            time.sleep(0.2)
            QApplication.processEvents()
        
        print("✓ Loading complete!")
        time.sleep(0.5)
        splash.close()
        app.quit()
    
    QTimer.singleShot(500, simulate_loading)
    sys.exit(app.exec())


def test_message_only():
    """Test splash with messages only (no percentage)"""
    print("=" * 60)
    print("SPLASH SCREEN TEST - Message Only Mode")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    splash = SplashScreen(
        show_percentage=False,
        show_message=True,
        app_name="Financial Manager",
        version="1.0.0"
    )
    
    splash.show()
    print("✓ Message-only splash screen shown")
    
    messages = [
        (20, "Starting up..."),
        (40, "Loading components..."),
        (60, "Initializing services..."),
        (80, "Almost ready..."),
        (100, "Launch!")
    ]
    
    def simulate_loading():
        for progress, message in messages:
            splash.set_progress(progress, message)
            print(f"  {message}")
            time.sleep(0.6)
            QApplication.processEvents()
        
        print("✓ Loading complete!")
        time.sleep(0.5)
        splash.close()
        app.quit()
    
    QTimer.singleShot(500, simulate_loading)
    sys.exit(app.exec())


def test_custom_size():
    """Test splash with custom size"""
    print("=" * 60)
    print("SPLASH SCREEN TEST - Custom Size (Wide)")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    splash = SplashScreen(
        show_percentage=True,
        show_message=True,
        app_name="Financial Manager Pro",
        version="2.0.0",
        width=800,   # Wider
        height=500   # Taller
    )
    
    splash.show()
    print("✓ Wide splash screen shown (800x500)")
    
    def simulate_loading():
        for i in range(0, 101, 10):
            splash.set_progress(i, f"Loading... {i}% complete")
            time.sleep(0.3)
            QApplication.processEvents()
        
        print("✓ Loading complete!")
        time.sleep(0.5)
        splash.close()
        app.quit()
    
    QTimer.singleShot(500, simulate_loading)
    sys.exit(app.exec())


def run_all_tests():
    """Run all test modes in sequence"""
    print("\n" + "=" * 60)
    print("RUNNING ALL SPLASH SCREEN TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        ("Basic (Full Featured)", test_basic_splash),
        ("Minimal (No Info)", test_minimal_splash),
        ("Percentage Only", test_percentage_only),
        ("Message Only", test_message_only),
        ("Custom Size", test_custom_size)
    ]
    
    for i, (name, test_func) in enumerate(tests, 1):
        print(f"\nTest {i}/{len(tests)}: {name}")
        input("Press Enter to run this test...")
        test_func()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED!")
    print("=" * 60)


def main():
    """Main test runner with menu"""
    print("\n" + "=" * 60)
    print("SPLASH SCREEN TEST SUITE")
    print("=" * 60)
    print("\nSelect a test to run:")
    print("  1. Basic splash (all features)")
    print("  2. Minimal splash (no percentage/message)")
    print("  3. Percentage only")
    print("  4. Message only")
    print("  5. Custom size (wide)")
    print("  6. Run all tests in sequence")
    print("  0. Exit")
    print("=" * 60)
    
    choice = input("\nEnter choice (0-6): ").strip()
    
    tests = {
        '1': test_basic_splash,
        '2': test_minimal_splash,
        '3': test_percentage_only,
        '4': test_message_only,
        '5': test_custom_size,
        '6': run_all_tests,
    }
    
    if choice == '0':
        print("Exiting...")
        return
    
    test_func = tests.get(choice)
    if test_func:
        print("\n")
        test_func()
    else:
        print("Invalid choice. Please select 0-6.")
        main()


if __name__ == "__main__":
    main()
