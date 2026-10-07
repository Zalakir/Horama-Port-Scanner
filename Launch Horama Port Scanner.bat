@echo off
setlocal

set "SCRIPT=%~dp0HoramaPortScanner_v1.0.py"

if not exist "%SCRIPT%" (
    echo Could not find the Horama Port Scanner script:
    echo "%SCRIPT%"
    pause
    exit /b 1
)

where pyw.exe >nul 2>&1
if not errorlevel 1 (
    start "" pyw.exe -3 "%SCRIPT%"
    exit /b 0
)

where pythonw.exe >nul 2>&1
if not errorlevel 1 (
    start "" pythonw.exe "%SCRIPT%"
    exit /b 0
)

echo Python was not found. Install Python 3 and make sure its launcher is on PATH.
pause
exit /b 1
