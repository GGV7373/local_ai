@echo off
REM Start the Audio Gateway Server
echo Starting Audio Gateway Server...
cd /d "%~dp0gateway"
python server.py
pause
