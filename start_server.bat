@echo off
title MediTriage AI Server
echo ====================================================
echo      Starting MediTriage AI Clinical Copilot
echo ====================================================
echo.
echo Application will be available at:
echo   - Local PC:       http://127.0.0.1:5000
echo   - Mobile Wi-Fi:   http://192.168.1.106:5000
echo.
echo (Press Ctrl + C in this window to stop the server)
echo ====================================================
echo.
cd /d "%~dp0"
python app.py
pause
