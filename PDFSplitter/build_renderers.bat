@echo off
setlocal enabledelayedexpansion

REM Collect all settings.json files in editor\renderers\*\settings.json
set "ADDDATA="
for /f "delims=" %%f in ('dir /b /s /a-d editor\\renderers\\*\\settings.json') do (
    REM Get the relative path to the renderer subfolder
    set "RENDERER=%%~dpf"
    set "RENDERER=!RENDERER:%CD%\\editor\\renderers\\=!"
    set "RENDERER=!RENDERER:settings.json=!"
    set "RENDERER=!RENDERER:~0,-1!"
    if not "!RENDERER!"=="" (
        set "ADDDATA=!ADDDATA! --add-data=%%f:editor/renderers/!RENDERER!"
    ) else (
        echo Skipping invalid renderer path for %%f
    )
)

REM Add other data files
set "ADDDATA=!ADDDATA! --add-data=readme.md:. --add-data=.env:."

REM Add CEF Python resources if they exist
if exist "%LOCALAPPDATA%\pyinstaller\cache\cefpython3" (
    echo Found CEF Python cache, adding CEF resources...
    set "ADDDATA=!ADDDATA! --add-data=%LOCALAPPDATA%\pyinstaller\cache\cefpython3\locales:locales"
    set "ADDDATA=!ADDDATA! --add-data=%LOCALAPPDATA%\pyinstaller\cache\cefpython3\*.pak:."
    set "ADDDATA=!ADDDATA! --add-data=%LOCALAPPDATA%\pyinstaller\cache\cefpython3\*.bin:."
    set "ADDDATA=!ADDDATA! --add-data=%LOCALAPPDATA%\pyinstaller\cache\cefpython3\*.dat:."
    set "ADDDATA=!ADDDATA! --add-data=%LOCALAPPDATA%\pyinstaller\cache\cefpython3\*.dll:."
) else if exist "%PYTHONPATH%\Lib\site-packages\cefpython3" (
    echo Found CEF Python in site-packages, adding CEF resources...
    set "ADDDATA=!ADDDATA! --add-data=%PYTHONPATH%\Lib\site-packages\cefpython3\locales:locales"
    set "ADDDATA=!ADDDATA! --add-data=%PYTHONPATH%\Lib\site-packages\cefpython3\*.pak:."
    set "ADDDATA=!ADDDATA! --add-data=%PYTHONPATH%\Lib\site-packages\cefpython3\*.bin:."
    set "ADDDATA=!ADDDATA! --add-data=%PYTHONPATH%\Lib\site-packages\cefpython3\*.dat:."
    set "ADDDATA=!ADDDATA! --add-data=%PYTHONPATH%\Lib\site-packages\cefpython3\*.dll:."
)

REM Run pyinstaller with hidden imports for CEF
pyinstaller --onefile --name PDFUtility_ALPHA_Build-1-0-0_7172025 --collect-submodules editor.renderers --hidden-import=cefpython3 !ADDDATA! pdfSplitter.py
pause
endlocal