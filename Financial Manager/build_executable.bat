@echo off
REM PyInstaller Build Script for Financial Manager
REM This script builds a standalone executable with all dependencies and assets

setlocal enabledelayedexpansion

echo ========================================
echo Financial Manager - PyInstaller Build
echo ========================================
echo.

REM Set project root
set "PROJECT_ROOT=%~dp0"
echo Project Root: %PROJECT_ROOT%

REM Check if PyInstaller is installed
py -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    py -m pip install pyinstaller -q
    if errorlevel 1 (
        echo Failed to install PyInstaller
        exit /b 1
    )
)

echo.
echo Building executable...
echo.

REM Create temporary spec file location
set "SPEC_PATH=%TEMP%\fm_build"
if not exist "%SPEC_PATH%" mkdir "%SPEC_PATH%"

REM Build command with all necessary data files and configurations
py -m PyInstaller ^
    --name "FinancialManager" ^
    --onefile ^
    --windowed ^
    --icon "%PROJECT_ROOT%resources\icons\Rent_Tracker.ico" ^
    --add-data "%PROJECT_ROOT%resources;resources" ^
    --add-data "%PROJECT_ROOT%resources\icons;resources/icons" ^
    --add-data "%PROJECT_ROOT%ui;ui" ^
    --add-data "%PROJECT_ROOT%src;src" ^
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
    --hidden-import=json ^
    --hidden-import=datetime ^
    --hidden-import=pathlib ^
    --hidden-import=pyi_splash ^
    --collect-all=matplotlib ^
    --distpath "%PROJECT_ROOT%dist" ^
    --workpath "%PROJECT_ROOT%build" ^
    --specpath "%SPEC_PATH%" ^
    --noconfirm ^
    "%PROJECT_ROOT%main_window.py"

if errorlevel 1 (
    echo.
    echo Build failed!
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: %PROJECT_ROOT%dist\FinancialManager.exe
echo.

REM Optional: Run the executable
REM "%PROJECT_ROOT%dist\FinancialManager.exe"

pause
