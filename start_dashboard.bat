@echo off
title AgroTrack Farmer Dashboard
cd /d "C:\Users\HP\.gemini\antigravity\scratch\farmer_dashboard"
echo ========================================================
echo   Starting AgroTrack Farmer Performance Dashboard...
echo ========================================================
echo Opening browser to http://127.0.0.1:8080/ ...
start http://127.0.0.1:8080/
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8080
pause
