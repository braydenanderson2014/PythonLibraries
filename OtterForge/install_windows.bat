@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "LOG_FILE=%SCRIPT_DIR%install_windows_launcher.log"
set "SHOULD_PAUSE=1"

for %%A in (%*) do (
  if /I "%%~A"=="-NoPause" set "SHOULD_PAUSE=0"
)

echo === OtterForge Installer Launcher ===
echo Script directory: %SCRIPT_DIR%
echo Log file: %LOG_FILE%
echo.

where powershell >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo ERROR: powershell executable not found in PATH.
  echo This launcher cannot continue.
  if %SHOULD_PAUSE% neq 0 pause
  exit /b 1
)

echo [%DATE% %TIME%] Launcher started>>"%LOG_FILE%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install_windows.ps1" %*
set "EXITCODE=%ERRORLEVEL%"
echo [%DATE% %TIME%] Launcher exit code: %EXITCODE%>>"%LOG_FILE%"

if %EXITCODE% neq 0 (
  echo.
  echo OtterForge installation failed. Check the error messages above.
  echo See launcher log: %LOG_FILE%
  if %SHOULD_PAUSE% neq 0 pause
  exit /b %EXITCODE%
)

echo OtterForge installation succeeded.
if %SHOULD_PAUSE% neq 0 pause
exit /b 0