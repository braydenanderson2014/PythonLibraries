# Splash Screen Integration Instructions

## Overview
Your PyInstaller build includes a splash screen that displays during application startup.
**IMPORTANT:** The splash screen must be manually closed from your Python code.

## Required Code Addition

Add this code to your main application file (`main_application.py`) after your application has finished initializing:

```python
# Close PyInstaller splash screen (if present)
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    # Not running as PyInstaller executable, or splash not enabled
    pass
```

## Recommended Placement

### For GUI Applications (Tkinter, PyQt, etc.)
Place the code after your main window is created and displayed:

```python
import tkinter as tk

# Create your main window
root = tk.Tk()
root.title("Your Application")

# Configure your GUI
# ... your GUI setup code ...

# Show the main window
root.deiconify()  # If you hid it initially
root.update()     # Force window to display

# Close splash screen after GUI is ready
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

# Start main loop
root.mainloop()
```

### For Console Applications
Place the code after your application has finished loading:

```python
# Your imports and initialization
import sys
import os

# Application setup
print("Loading application...")
# ... your setup code ...

# Close splash screen after loading is complete
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

print("Application ready!")
# ... rest of your application ...
```

### Advanced: Update Splash Screen Text
You can also update the splash screen text before closing it:

```python
try:
    import pyi_splash
    
    # Update splash text (optional)
    pyi_splash.update_text("Loading complete...")
    
    # Close the splash screen
    pyi_splash.close()
except ImportError:
    pass
```

## Common Issues

1. **Splash screen doesn't close:** Make sure the close code is reachable and executed
2. **Error messages:** The ImportError handling ensures no errors if running without PyInstaller
3. **Timing:** Place the close code after your application is fully ready, not during early initialization

## Testing

- **Development:** The splash code will be ignored when running directly with Python
- **Built executable:** The splash screen will display and close as configured

Generated for build: PDF Utility-08042025-ALPHA
Date: 2025-08-04 23:41:43
