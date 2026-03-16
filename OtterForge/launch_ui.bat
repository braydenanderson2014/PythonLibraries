@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul

set "PY_CMD="
where python >nul 2>&1 && set "PY_CMD=python"
if not defined PY_CMD (
  where py >nul 2>&1 && set "PY_CMD=py -3"
)

if not defined PY_CMD (
  echo Python was not found on PATH.
  popd >nul
  exit /b 1
)

%PY_CMD% -m otterforge ui
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo UI launch failed. If needed, install PyQt6 with: pip install PyQt6
)

popd >nul
exit /b %EXIT_CODE%
