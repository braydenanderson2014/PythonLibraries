@echo off
setlocal

rem Allow launching web UI even if run.bat loop is active, but warn user.
powershell -NoProfile -Command "$runLoopRunning = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(\.exe)?$' -and $_.CommandLine -match 'main\.py' -and $_.CommandLine -match '\brun\b' -and $_.CommandLine -notmatch '\bstatus\b' -and $_.CommandLine -notmatch '\bdevices\b' -and $_.CommandLine -notmatch '\bwater\b' -and $_.CommandLine -notmatch '\bstop\b' -and $_.CommandLine -notmatch '\bweb\b' }; if ($runLoopRunning) { exit 0 } else { exit 1 }"
if %errorlevel%==0 (
	echo Warning: A run-loop process is already active. Web UI will still launch as requested.
)

python "%~dp0main.py" --config "%~dp0config.json" web --host 0.0.0.0 --open-browser %*
