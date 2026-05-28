@echo off
setlocal

rem If the web UI is already running, do not start a second controller loop.
powershell -NoProfile -Command "$webUiRunning = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(\.exe)?$' -and $_.CommandLine -match 'main\.py' -and $_.CommandLine -match '\bweb\b' }; if ($webUiRunning) { exit 0 } else { exit 1 }"
if %errorlevel%==0 (
	echo Web UI automation is already running. Skipping run.bat to avoid duplicate controller loops.
	exit /b 0
)

python "%~dp0main.py" --config "%~dp0config.json" run %*
