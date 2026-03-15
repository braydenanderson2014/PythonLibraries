# PyInstaller Build Guide for Financial Manager

## Overview
This guide explains how to build a standalone executable for the Financial Manager application using PyInstaller.

## What's Included in the Build

### Data Directories
- **ui/** - All UI modules and dialogs
- **src/** - All backend Python modules (database, trackers, calculations, etc.)
- **resources/icons/** - Application icons (PNG files, ICO files)
- **resources/Splash.png** - Splash screen image

### Excluded (As Requested)
- JSON configuration files (settings.json, etc.)
- Help documentation files
- Test files and examples
- Build artifacts

## Prerequisites

1. **Python 3.8+** installed
2. **All dependencies installed** from requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

3. **PyInstaller** (will be installed automatically if missing):
   ```bash
   pip install pyinstaller
   ```

## Building the Executable

### Option 1: Using Batch Script (Windows)
Simply double-click the batch file:
```batch
build_executable.bat
```

Or run from command line:
```cmd
cd "C:\Users\brayd\OneDrive\Documents\GitHub\SystemCommands\Python Projects\Financial Manager"
build_executable.bat
```

### Option 2: Using Python Script (Cross-Platform)
```bash
cd "C:\Users\brayd\OneDrive\Documents\GitHub\SystemCommands\Python Projects\Financial Manager"
python build_executable.py
```

### Option 3: Manual PyInstaller Command

```bash
pyinstaller ^
    --name="FinancialManager" ^
    --onefile ^
    --windowed ^
    --icon="resources\icons\Rent_Tracker.ico" ^
    --splash="resources\Splash.png" ^
    --add-data "resources\icons;resources/icons" ^
    --add-data "resources\Splash.png;resources" ^
    --add-data "ui;ui" ^
    --add-data "src;src" ^
    --hidden-import=PyQt6 ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=matplotlib ^
    --hidden-import=matplotlib.backends.backend_qt5agg ^
    --hidden-import=openpyxl ^
    --hidden-import=requests ^
    --hidden-import=pandas ^
    --hidden-import=numpy ^
    --hidden-import=sqlite3 ^
    --collect-all=matplotlib ^
    --distpath "dist" ^
    --buildpath "build" ^
    --specpath "." ^
    --noconfirm ^
    main_window.py
```

## Build Output

After successful build, you'll find:

- **dist/FinancialManager.exe** - The standalone executable (this is what you run)
- **build/** - Temporary build files (can be deleted)
- **FinancialManager.spec** - Build specification file

## Running the Application

Simply double-click:
```
dist/FinancialManager.exe
```

Or run from command line:
```cmd
dist\FinancialManager.exe
```

## Troubleshooting

### Build Fails with "file not found"
- Ensure you're in the correct project directory
- Verify all source files exist
- Check that resources/icons/Rent_Tracker.ico exists

### Missing Splash Screen
- The splash screen is optional and the build will continue without it
- If you want it, ensure resources/Splash.png exists

### Runtime Errors with Matplotlib
- This is handled by `--collect-all=matplotlib`
- Ensure matplotlib is installed: `pip install matplotlib`

### Database/File Access Issues
- The executable needs write permissions in its working directory
- Place it in a user-writable location

### Missing Qt Libraries
- All Qt6 components are included via hidden imports
- If issues persist, reinstall: `pip install PyQt6 --force-reinstall`

## File Structure in Executable

When PyInstaller creates the executable, it bundles:
```
FinancialManager.exe (single file)
├── ui/ (all UI modules)
├── src/ (all backend modules)
├── resources/icons/ (images)
└── [standard library + all pip packages]
```

## Size and Performance

- **Executable Size**: ~300-400 MB (typical for PyQt6 + scientific stack)
- **First Launch**: May take 5-10 seconds as it extracts and initializes
- **Subsequent Launches**: Much faster, typically 1-2 seconds

## Distribution

To share the application:
1. Simply provide `dist/FinancialManager.exe`
2. Users don't need Python installed
3. Include a README with basic requirements (Windows OS, ~400MB disk space)

## Notes

- The executable is for **Windows only** (uses .exe format)
- For macOS: Change `--icon` to `.icns` file and `--windowed` works as-is
- For Linux: Use `.png` for icon and adjust path separators
- Database and configuration files are stored in user's AppData (Windows) or similar location, not in the exe directory

## Rebuilding

To rebuild after code changes:
1. Simply run the build script again
2. Delete the old `dist/FinancialManager.exe` first
3. PyInstaller will create a fresh executable

## Advanced Options

For production builds, you might also consider:
- Code signing the executable
- Creating an installer (NSIS, InnoSetup)
- Code obfuscation
- Compression options in PyInstaller

For more info: https://pyinstaller.org/
