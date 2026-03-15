@echo off
echo Running PyQt PDF Utility...

:: Add the PDFUtility directory to the Python path so we can import modules
set PYTHONPATH=%PYTHONPATH%;%~dp0..\PDFUtility

:: Run the application with the correct Python version and pass all arguments
py -3.13 "%~dp0build_gui_interface.py" %*

:: Check for errors
if %ERRORLEVEL% NEQ 0 (
    echo Error running build script
    pause
    exit /b %ERRORLEVEL%
)
