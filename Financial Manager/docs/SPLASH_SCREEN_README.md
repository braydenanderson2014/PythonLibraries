# Splash Screen Component Documentation

## Overview
A modern, Adobe-style splash screen component for the Financial Manager application. Features smooth animations, customizable display options, and modular design.

## Features

### ✨ Core Features
- **Background Image Support**: Load custom splash images or use default gradient
- **Animated Progress Bar**: Smooth progress animations with gradient effects
- **Optional Percentage Display**: Toggle to show/hide progress percentage
- **Optional Message Display**: Toggle to show/hide loading status messages
- **Modular Design**: Easy to integrate and customize
- **Professional Styling**: Clean, modern aesthetic similar to Adobe products

### 🎨 Visual Elements
- Custom gradient progress bar with smooth animations
- Dark theme with semi-transparent overlays
- Application name and version display
- Copyright/info footer
- Smooth easing curves for animations

## Installation

The component is located at: `/assets/SplashScreen.py`

No additional dependencies required beyond PyQt6.

## Basic Usage

### Simple Example
```python
from assets.SplashScreen import SplashScreen
from PyQt6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)

# Create splash screen with default settings
splash = SplashScreen()
splash.show()

# Your loading code here
splash.set_progress(50, "Loading database...")

# Close when done
splash.finish()

sys.exit(app.exec())
```

### Advanced Example
```python
from assets.SplashScreen import SplashScreen

# Create splash with custom settings
splash = SplashScreen(
    image_path="resources/splash_background.png",  # Custom image
    show_percentage=True,                          # Show percentage
    show_message=True,                             # Show status messages
    app_name="Financial Manager Pro",              # Custom app name
    version="2.0.0",                               # Version number
    width=700,                                     # Custom width
    height=450                                     # Custom height
)

splash.show()

# Update progress with message
splash.set_progress(25, "Initializing database...")
splash.set_progress(50, "Loading user preferences...")
splash.set_progress(75, "Setting up UI...")
splash.set_progress(100, "Ready!")

# Close and show main window
splash.finish(main_window)
```

## API Reference

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_path` | str\|None | None | Path to background image. If None, uses gradient. |
| `show_percentage` | bool | True | Show percentage below progress bar |
| `show_message` | bool | True | Show status message below progress bar |
| `app_name` | str | "Financial Manager" | Application name to display |
| `version` | str | "1.0.0" | Version string to display |
| `width` | int | 600 | Splash screen width in pixels |
| `height` | int | 400 | Splash screen height in pixels |

### Methods

#### `set_progress(value, message=None)`
Update the progress bar and optionally the status message.

**Parameters:**
- `value` (int): Progress value from 0 to 100
- `message` (str, optional): Status message to display

**Example:**
```python
splash.set_progress(50, "Loading database...")
```

#### `set_message(message)`
Update only the status message without changing progress.

**Parameters:**
- `message` (str): Status message to display

**Example:**
```python
splash.set_message("Connecting to server...")
```

#### `get_progress()`
Get the current progress value.

**Returns:**
- int: Current progress (0-100)

#### `get_message()`
Get the current status message.

**Returns:**
- str: Current status message

#### `finish(main_window=None)`
Close the splash screen with fade out animation.

**Parameters:**
- `main_window` (QWidget, optional): Main window to show after closing splash

**Example:**
```python
splash.finish(main_window)
```

## Customization

### Toggle Features

You can enable/disable features via constructor:

```python
# Percentage only, no messages
splash = SplashScreen(show_percentage=True, show_message=False)

# Messages only, no percentage
splash = SplashScreen(show_percentage=False, show_message=True)

# Neither (minimal)
splash = SplashScreen(show_percentage=False, show_message=False)
```

### Custom Background Image

#### Requirements:
- Format: PNG, JPG, or any Qt-supported image format
- Recommended size: Match your width/height parameters
- The image will be scaled and cropped to fit

```python
splash = SplashScreen(
    image_path="/path/to/your/splash.png",
    width=800,
    height=600
)
```

### Styling

The component uses internal styling, but you can modify colors in the source code:

**Progress Bar Colors:**
```python
# In ModernProgressBar class
self.progress_gradient_start = QColor(0, 122, 255)  # Blue
self.progress_gradient_end = QColor(0, 180, 255)    # Light blue
```

**Background Gradient:**
```python
# In _create_background method
gradient.setColorAt(0, QColor(15, 32, 52))   # Top color
gradient.setColorAt(1, QColor(8, 16, 28))    # Bottom color
```

## Integration Patterns

### Pattern 1: Separate Loading Thread
```python
from PyQt6.QtCore import QThread, pyqtSignal

class LoadingThread(QThread):
    progress_updated = pyqtSignal(int, str)
    
    def run(self):
        self.progress_updated.emit(10, "Loading config...")
        # ... loading code ...
        self.progress_updated.emit(50, "Loading data...")
        # ... more loading ...
        self.progress_updated.emit(100, "Complete!")

# In your main app
loading_thread = LoadingThread()
loading_thread.progress_updated.connect(
    lambda v, m: splash.set_progress(v, m)
)
loading_thread.start()
```

### Pattern 2: Step-by-Step Loading
```python
def initialize_app(splash):
    steps = [
        (load_config, "Loading configuration..."),
        (init_database, "Initializing database..."),
        (load_user_data, "Loading user data..."),
        (setup_ui, "Setting up interface..."),
    ]
    
    progress_per_step = 100 // len(steps)
    
    for i, (func, message) in enumerate(steps):
        splash.set_progress((i + 1) * progress_per_step, message)
        func()  # Execute the loading function

# Usage
initialize_app(splash)
splash.finish(main_window)
```

### Pattern 3: With Main Window Integration
```python
from PyQt6.QtWidgets import QMainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... window setup ...

# Application startup
app = QApplication(sys.argv)

splash = SplashScreen()
splash.show()

# Simulate initialization
splash.set_progress(33, "Loading modules...")
QApplication.processEvents()

splash.set_progress(66, "Building interface...")
main_window = MainWindow()
QApplication.processEvents()

splash.set_progress(100, "Ready!")
splash.finish(main_window)

main_window.show()
sys.exit(app.exec())
```

## Testing

Run the component standalone to see the demo:

```bash
python assets/SplashScreen.py
```

This will show a splash screen with simulated loading progress.

## Best Practices

### 1. Keep Messages Short
Status messages should be concise and meaningful:
- ✅ "Loading database..."
- ✅ "Initializing modules..."
- ❌ "Please wait while we load the database and initialize all the necessary components..."

### 2. Update Progress Regularly
Update progress at logical checkpoints:
```python
splash.set_progress(0, "Starting...")
splash.set_progress(25, "Loading config...")
splash.set_progress(50, "Loading data...")
splash.set_progress(75, "Building UI...")
splash.set_progress(100, "Ready!")
```

### 3. Process Events
Always process events after updates to ensure smooth display:
```python
splash.set_progress(50, "Loading...")
QApplication.processEvents()
```

### 4. Don't Block the UI Thread
For long operations, use QThread or QTimer:
```python
QTimer.singleShot(0, lambda: heavy_loading_function())
```

### 5. Minimum Display Time
Consider showing splash for a minimum time for branding:
```python
splash.show()
start_time = time.time()

# ... loading code ...

# Ensure splash shows for at least 2 seconds
elapsed = time.time() - start_time
if elapsed < 2.0:
    time.sleep(2.0 - elapsed)

splash.finish(main_window)
```

## Troubleshooting

### Splash doesn't update
**Problem:** Progress bar doesn't update during loading.

**Solution:** Call `QApplication.processEvents()` after each update:
```python
splash.set_progress(50, "Loading...")
QApplication.processEvents()  # Add this!
```

### Background image doesn't show
**Problem:** Custom image not displaying.

**Solution:** 
1. Check file path is correct
2. Verify image format is supported (PNG, JPG)
3. Check file permissions
4. Verify image file exists

### Splash closes immediately
**Problem:** Splash closes before loading is visible.

**Solution:** Ensure your main event loop hasn't started yet, or use QTimer for delayed loading.

## Future Enhancements

Potential features for future versions:
- [ ] Fade in/out animations
- [ ] Multiple progress bars for parallel operations
- [ ] Animated logo/icon support
- [ ] Theme customization (light/dark)
- [ ] Blur effect for background
- [ ] Loading spinner option
- [ ] Sound effects on completion
- [ ] Custom fonts support
- [ ] Internationalization support

## Example Screenshots

### Default Gradient Background
```
┌────────────────────────────────────────┐
│                                        │
│                                        │
│                                        │
│                                        │
│           [Gradient Background]        │
│                                        │
│                                        │
│  Financial Manager           v1.0.0    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  50%              Loading database...  │
│                                        │
│  © 2026 Financial Manager             │
└────────────────────────────────────────┘
```

### With Custom Image
```
┌────────────────────────────────────────┐
│                                        │
│        [Your Custom Splash Image]      │
│                                        │
│                                        │
│                                        │
│                                        │
│                                        │
│  Financial Manager Pro       v2.0.0    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  75%              Setting up UI...     │
│                                        │
│  © 2026 Financial Manager             │
└────────────────────────────────────────┘
```

## License

Part of the Financial Manager application. Internal use only.

## Support

For issues or questions, refer to the main application documentation or contact the development team.
