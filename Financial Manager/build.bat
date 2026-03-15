@echo off
echo Building FinancialManager...
FinancialManager_env\Scripts\python.exe ..\build_cli.py --template pyqt6guiapplication --profile prod --start build
pause
