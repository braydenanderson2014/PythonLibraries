import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

try:
    from PyQt6.QtCore import QUrl, QTimer
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    print("PyQt6 WebEngine is available!")
except ImportError as e:
    print(f"PyQt6 WebEngine import error: {e}")

print("Script completed.")
