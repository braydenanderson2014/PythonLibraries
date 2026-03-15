#!/usr/bin/env python3
import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)

try:
    from PyQt6.QtWidgets import QApplication
    print("✅ PyQt6 import successful!")
except ImportError as e:
    print("❌ PyQt6 import failed:", e)
    sys.exit(1)
except Exception as e:
    print("❌ Other error:", e)
    sys.exit(1)

print("Test complete!")
