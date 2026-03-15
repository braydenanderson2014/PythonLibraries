@echo off
REM Notification Daemon Launcher for Financial Manager
REM This script activates the virtual environment and runs the notification daemon

cd /d "D:\Financial Manager"

REM Activate virtual environment
call "FinancialManager_env\Scripts\activate.bat"

REM Check if we want to run a test or the full daemon
if "%1"=="test" (
    echo Running notification test...
    python notification_daemon.py --test
    pause
) else if "%1"=="log" (
    echo Starting daemon with logging...
    python notification_daemon.py --log "logs\notification_daemon.log"
) else (
    echo Starting notification daemon...
    echo Press Ctrl+C to stop the daemon
    python notification_daemon.py
)

pause
