# Financial Manager - PyInstaller Quick Build

## Quick Start (30 seconds)

```batch
REM Open PowerShell or Command Prompt in the Financial Manager folder, then:
python build_executable.py
```

**OR**

Double-click: `build_executable.bat`

## What Gets Included

✅ All Python UI modules (35+ files)
✅ All Backend modules (30+ files)  
✅ Application icons (PNG, ICO)
✅ Splash screen
✅ All dependencies (PyQt6, Pandas, Matplotlib, etc.)

❌ JSON config files (can be recreated on first run)
❌ Help documentation
❌ Test files
❌ Database (created on first run)

## Output

- **dist/FinancialManager.exe** ← This is your executable!
- Run it anytime, no Python installation needed

## Command Reference

### Batch File (Windows)
```batch
build_executable.bat
```

### Python Script (Any OS)
```bash
python build_executable.py
```

### Full Manual Command
```bash
pyinstaller --name="FinancialManager" --onefile --windowed ^
    --icon="resources\icons\Rent_Tracker.ico" ^
    --splash="resources\Splash.png" ^
    --add-data "resources\icons;resources/icons" ^
    --add-data "ui;ui" ^
    --add-data "src;src" ^
    --hidden-import=PyQt6 --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=matplotlib --hidden-import=matplotlib.backends.backend_qt5agg ^
    --hidden-import=openpyxl --hidden-import=requests ^
    --hidden-import=pandas --hidden-import=numpy ^
    --collect-all=matplotlib main_window.py
```

## Includes Everything From

```
Financial Manager/
├── ui/                    ✅ All 35+ UI modules
├── src/                   ✅ All 30+ backend modules  
├── resources/
│   ├── icons/            ✅ Images (PNG, ICO)
│   └── Splash.png        ✅ Splash screen
└── main_window.py        ✅ Entry point
```

## File Size & Performance

- **Size**: ~300-400 MB
- **First Run**: 5-10 seconds
- **Subsequent**: 1-2 seconds
- **Runs**: Windows only

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Build fails | Check you're in correct folder, all files exist |
| No splash screen | Optional - build continues without it |
| File not found | Verify `resources/icons/Rent_Tracker.ico` exists |
| Slow startup | Normal - extracting PyQt6 + scientific libraries |

## Next Steps

1. Run build script → wait 2-5 minutes
2. Find exe in `dist/FinancialManager.exe`
3. Test it works
4. Distribute just the .exe file to users (no Python needed!)

---

**Full Guide**: See `PYINSTALLER_BUILD_GUIDE.md`
