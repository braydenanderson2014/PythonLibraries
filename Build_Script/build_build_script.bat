@echo off
echo Building PyInstaller Build Tool GUI...

:: Check if PyInstaller is available
py -3.13 -c "import PyInstaller" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller not found. Installing...
    py -3.13 -m pip install pyinstaller
)

:: Build the build tool itself with icon
py -3.13 -m PyInstaller ^
    --onefile ^
    --windowed ^
    --icon="Build_Script.ico" ^
    --name="PyInstaller_Build_Tool" ^
    --clean ^
    build_gui_interface.py

echo Build complete! Check the dist folder for PyInstaller_Build_Tool.exe
pause
