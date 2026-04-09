@echo off
setlocal

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

set VENV_PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
  echo Virtual environment not found at: %VENV_PYTHON%
  echo.
  echo Please run install_all_windows.bat first to set up the environment.
  pause
  exit /b 1
)

echo Launching Subtitle Tool GUI...
echo Using virtual environment Python: %VENV_PYTHON%
echo Using subtitle script: %SCRIPT_DIR%subtitle_ui.py
set "SUBTITLE_TOOL_TEMP_DIR=%SCRIPT_DIR%.runtime-temp"
if not exist "%SUBTITLE_TOOL_TEMP_DIR%" mkdir "%SUBTITLE_TOOL_TEMP_DIR%"
echo Using runtime temp directory: %SUBTITLE_TOOL_TEMP_DIR%
"%VENV_PYTHON%" subtitle_ui.py

if %ERRORLEVEL% neq 0 (
  echo.
  echo Failed to launch GUI. Exit code: %ERRORLEVEL%
  echo.
  echo If dependencies are missing, try running install_all_windows.bat again.
  pause
  exit /b %ERRORLEVEL%
)

exit /b 0
