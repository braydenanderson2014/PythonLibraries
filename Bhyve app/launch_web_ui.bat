@echo off
setlocal
python "%~dp0main.py" --config "%~dp0config.json" web --open-browser %*
