@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul

set "PY_CMD="
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
  set "PY_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe"
)

if not defined PY_CMD (
  where python >nul 2>&1 && set "PY_CMD=python"
)

if not defined PY_CMD (
  where py >nul 2>&1 && set "PY_CMD=py -3"
)

if not defined PY_CMD (
  echo Python was not found on PATH.
  echo Run install_windows.bat from the project root to create a local environment.
  popd >nul
  exit /b 1
)

%PY_CMD% -m otterforge ui
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    echo UI launch failed while using the project virtual environment.
  ) else (
    echo No project virtual environment was found.
  )
  echo Run install_windows.bat from the project root to create .venv and install dependencies.
)

popd >nul
exit /b %EXIT_CODE%