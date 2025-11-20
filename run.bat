@echo off
REM Shenzhen Weather Art Visualization - Portable run script
REM Prefer local .venv if available, otherwise fall back to python in PATH

setlocal
set PY_CMD=
if exist .venv\Scripts\python.exe (
    set "PY_CMD=.venv\Scripts\python.exe"
)
if "%PY_CMD%"=="" (
    set "PY_CMD=python"
)

echo Starting Shenzhen Weather Art Visualization...
%PY_CMD% src/main.py %*

if errorlevel 1 (
        echo.
    echo Run failed. Please check:
    echo 1. Is the Python environment configured correctly?
    echo 2. Are dependencies installed? ^(pip install -r requirements.txt^)
    echo 3. Is the network connection working?
        pause
)
endlocal