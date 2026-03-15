@echo off
echo Running PyQt PDF Utility...

:: Add the PDFSplitter directory to the Python path so we can import modules
set PYTHONPATH=%PYTHONPATH%;%~dp0..\PDFUtility

:: Run the application with the correct Python version
py -3.13 "%~dp0main_application.py"

if %ERRORLEVEL% NEQ 0 (
    echo Error running PDF Utility
    pause
    exit /b %ERRORLEVEL%
)
