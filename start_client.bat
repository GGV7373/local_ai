@echo off
REM Start the Desktop Client
echo Starting Desktop Client...
cd /d "%~dp0client"
python main.py
pause
