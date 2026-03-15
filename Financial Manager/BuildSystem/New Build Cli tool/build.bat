@echo off
REM Build script for BuildCLI using PyInstaller

echo Building BuildCLI executable...

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller
        exit /b 1
    )
)

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del "*.spec"

echo Cleaning completed.

REM Build the executable
echo Building executable...
python -m PyInstaller ^
    --onefile ^
    --console ^
    --name buildcli ^
    --distpath dist ^
    --workpath build ^
    --specpath . ^
    --add-data "modules;modules" ^
    --add-data "core;core" ^
    --add-data "utils;utils" ^
    --hidden-import asyncio ^
    --hidden-import importlib.util ^
    --hidden-import modules.system ^
    --hidden-import modules.pyinstaller_module ^
    --clean ^
    --noconfirm ^
    main.py

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable location: dist\buildcli.exe

REM Test the executable
echo.
echo Testing executable...
dist\buildcli.exe --version

if errorlevel 1 (
    echo Warning: Executable test failed
) else (
    echo Executable test passed!
)

echo.
echo Build process completed.
pause