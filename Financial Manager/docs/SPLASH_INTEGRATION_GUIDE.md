# Splash Screen Integration Guide

## Quick Integration Steps

When you're ready to integrate the splash screen into the main application, follow these steps:

## 1. Basic Integration (Simplest)

### In your main startup file (e.g., `main_window.py` or `__main__.py`):

```python
from PyQt6.QtWidgets import QApplication
from assets.SplashScreen import SplashScreen
import sys

def main():
    app = QApplication(sys.argv)
    
    # Create and show splash
    splash = SplashScreen(
        show_percentage=True,
        show_message=True,
        app_name="Financial Manager",
        version="1.0.0"
    )
    splash.show()
    
    # Initialize your application
    splash.set_progress(20, "Loading configuration...")
    from src.config import load_config
    config = load_config()
    
    splash.set_progress(40, "Initializing database...")
    from src.database import Database
    db = Database()
    
    splash.set_progress(60, "Loading user data...")
    # ... your loading code ...
    
    splash.set_progress(80, "Building interface...")
    from ui.main_window import MainWindow
    main_window = MainWindow()
    
    splash.set_progress(100, "Ready!")
    
    # Close splash and show main window
    splash.finish(main_window)
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

## 2. Advanced Integration (Threaded Loading)

### Create a loading worker:

```python
from PyQt6.QtCore import QThread, pyqtSignal

class ApplicationLoader(QThread):
    """Thread to handle application initialization without blocking UI"""
    progress_updated = pyqtSignal(int, str)
    loading_complete = pyqtSignal(object)  # Emits main window when ready
    loading_failed = pyqtSignal(str)  # Emits error message
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            # Step 1: Load configuration
            self.progress_updated.emit(10, "Loading configuration...")
            from src.config import load_config
            config = load_config()
            
            # Step 2: Initialize database
            self.progress_updated.emit(25, "Initializing database...")
            from src.database import Database
            db = Database()
            
            # Step 3: Load services
            self.progress_updated.emit(40, "Loading services...")
            from services.banking_api import BankingAPI
            banking = BankingAPI()
            
            # Step 4: Load user data
            self.progress_updated.emit(55, "Loading user data...")
            # ... load user data ...
            
            # Step 5: Initialize managers
            self.progress_updated.emit(70, "Initializing managers...")
            # ... initialize various managers ...
            
            # Step 6: Build UI
            self.progress_updated.emit(85, "Building interface...")
            from ui.main_window import MainWindow
            main_window = MainWindow()
            
            # Step 7: Finalize
            self.progress_updated.emit(100, "Ready!")
            
            # Emit the main window
            self.loading_complete.emit(main_window)
            
        except Exception as e:
            self.loading_failed.emit(str(e))


# In your main startup code:
def main():
    app = QApplication(sys.argv)
    
    # Create splash
    splash = SplashScreen(
        show_percentage=True,
        show_message=True
    )
    splash.show()
    
    # Create loader thread
    loader = ApplicationLoader()
    
    # Connect signals
    loader.progress_updated.connect(
        lambda progress, msg: splash.set_progress(progress, msg)
    )
    
    def on_loading_complete(main_window):
        splash.finish(main_window)
        main_window.show()
    
    def on_loading_failed(error_msg):
        splash.close()
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Startup Error", f"Failed to start application:\n{error_msg}")
        app.quit()
    
    loader.loading_complete.connect(on_loading_complete)
    loader.loading_failed.connect(on_loading_failed)
    
    # Start loading
    loader.start()
    
    sys.exit(app.exec())
```

## 3. Integration with Existing Main Window

### If you have an existing `main_window.py`:

```python
# Add to the top of main_window.py
from assets.SplashScreen import SplashScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... existing code ...
    
    @staticmethod
    def show_with_splash():
        """Factory method to create and show window with splash screen"""
        from PyQt6.QtWidgets import QApplication
        
        # Get or create QApplication instance
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create splash
        splash = SplashScreen()
        splash.show()
        
        # Initialize in steps
        splash.set_progress(25, "Creating main window...")
        main_window = MainWindow()
        
        splash.set_progress(50, "Loading preferences...")
        main_window.load_preferences()
        
        splash.set_progress(75, "Initializing components...")
        main_window.initialize_components()
        
        splash.set_progress(100, "Ready!")
        
        # Show window
        splash.finish(main_window)
        main_window.show()
        
        return main_window

# Then in your startup code:
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow.show_with_splash()
    sys.exit(app.exec())
```

## 4. Integration Points by File

### If your app structure is like this:

```
Financial Manager/
├── main_window.py          # Main entry point
├── assets/
│   └── SplashScreen.py    # ✓ Already here
├── ui/
│   ├── financial_tracker.py
│   └── ...
└── src/
    ├── database.py
    ├── bank.py
    └── ...
```

### Modify `main_window.py`:

Add at the beginning (after imports):
```python
from assets.SplashScreen import SplashScreen
```

Add in your main() or startup function:
```python
def main():
    app = QApplication(sys.argv)
    
    # ADD THIS:
    splash = SplashScreen(
        show_percentage=True,
        show_message=True,
        app_name="Financial Manager",
        version="1.0.0"
    )
    splash.show()
    QApplication.processEvents()
    
    # WRAP YOUR EXISTING INITIALIZATION WITH PROGRESS UPDATES:
    splash.set_progress(20, "Loading configuration...")
    # ... your config loading code ...
    
    splash.set_progress(40, "Initializing database...")
    # ... your database initialization ...
    
    splash.set_progress(60, "Loading UI components...")
    # ... your UI setup ...
    
    splash.set_progress(80, "Finalizing...")
    main_window = MainWindow()  # or your existing main window creation
    
    splash.set_progress(100, "Ready!")
    
    # ADD THIS:
    splash.finish(main_window)
    
    main_window.show()
    sys.exit(app.exec())
```

## 5. Custom Splash Image

### To use a custom background image:

1. **Create or obtain a splash image:**
   - Recommended size: 800x600 or 1024x768
   - Format: PNG (with transparency support) or JPG
   - Place it in: `assets/images/` or `resources/images/`

2. **Update the splash creation:**
```python
splash = SplashScreen(
    image_path="assets/images/splash_background.png",  # Your image path
    show_percentage=True,
    show_message=True,
    app_name="Financial Manager",
    version="1.0.0",
    width=800,  # Match your image size
    height=600
)
```

### Sample Image Creation (if you want to generate programmatically):

```python
from PIL import Image, ImageDraw, ImageFont
import os

def create_splash_image():
    """Create a simple splash image programmatically"""
    # Create image
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color=(15, 32, 52))
    draw = ImageDraw.Draw(img)
    
    # Add app name/logo
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    text = "Financial Manager"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    text_y = height // 2 - 50
    
    draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
    
    # Save
    os.makedirs('assets/images', exist_ok=True)
    img.save('assets/images/splash_background.png')
    print("Splash image created at: assets/images/splash_background.png")

# Run once to create the image
if __name__ == "__main__":
    create_splash_image()
```

## 6. Configuration Options

### Environment-based configuration:

```python
import os

# Development vs Production
DEBUG = os.getenv('DEBUG', 'False') == 'True'

splash = SplashScreen(
    show_percentage=DEBUG,      # Show percentage in debug mode
    show_message=DEBUG,          # Show messages in debug mode
    app_name="Financial Manager",
    version="1.0.0"
)

# In production, splash closes faster
if not DEBUG:
    # Quick loading without detailed messages
    splash.set_progress(50, "Loading...")
    # ... initialization ...
    splash.set_progress(100, "Ready!")
else:
    # Detailed loading steps
    splash.set_progress(10, "Loading config...")
    # ... each step with message ...
```

## 7. Error Handling

### Graceful error handling during startup:

```python
def main():
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    
    try:
        splash.set_progress(25, "Loading configuration...")
        config = load_config()
        
        splash.set_progress(50, "Initializing database...")
        db = Database()
        
        splash.set_progress(75, "Loading UI...")
        main_window = MainWindow()
        
        splash.set_progress(100, "Ready!")
        splash.finish(main_window)
        main_window.show()
        
    except Exception as e:
        splash.close()
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Startup Error",
            f"Failed to start application:\n\n{str(e)}\n\nPlease check logs for details."
        )
        return 1
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
```

## 8. Testing the Integration

### Test script:

```python
# test_splash_integration.py
import sys
import time
from PyQt6.QtWidgets import QApplication
from assets.SplashScreen import SplashScreen

def test_splash():
    """Test splash screen with simulated loading"""
    app = QApplication(sys.argv)
    
    splash = SplashScreen(
        show_percentage=True,
        show_message=True
    )
    splash.show()
    
    # Simulate loading steps
    steps = [
        (10, "Testing configuration..."),
        (30, "Testing database..."),
        (50, "Testing services..."),
        (70, "Testing UI components..."),
        (90, "Testing finalization..."),
        (100, "Test complete!")
    ]
    
    for progress, message in steps:
        splash.set_progress(progress, message)
        time.sleep(0.5)
        QApplication.processEvents()
    
    time.sleep(1)
    splash.close()
    
    print("✓ Splash screen test passed!")
    app.quit()

if __name__ == "__main__":
    test_splash()
```

## Summary

The splash screen is now ready to use! To integrate:

1. ✅ Import: `from assets.SplashScreen import SplashScreen`
2. ✅ Create: `splash = SplashScreen(...)`
3. ✅ Show: `splash.show()`
4. ✅ Update during loading: `splash.set_progress(50, "Loading...")`
5. ✅ Close: `splash.finish(main_window)`

The component is fully modular and won't affect your existing code until you choose to integrate it!
