@echo off
title Stop MediTriage AI Server
echo Stopping MediTriage AI server...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo Server stopped successfully.
pause
