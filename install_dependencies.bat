@echo off
REM Install all dependencies for Gateway and Client
echo Installing Audio Layer dependencies...
echo.

echo Installing Gateway dependencies...
cd /d "%~dp0gateway"
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install gateway dependencies!
    pause
    exit /b 1
)

echo.
echo Installing Client dependencies...
cd /d "%~dp0client"
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install client dependencies!
    pause
    exit /b 1
)

echo.
echo ========================================
echo All dependencies installed successfully!
echo ========================================
echo.
echo Next steps:
echo   1. Start the gateway: start_gateway.bat
echo   2. Start the client:  start_client.bat
echo.
pause
