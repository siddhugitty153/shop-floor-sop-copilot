@echo off
title BiztelAI SOP Copilot Launcher
echo ========================================================
echo   BiztelAI Shop-Floor SOP Copilot - Launcher
echo ========================================================
echo.
cd /d "%~dp0"

echo [1/2] Starting FastAPI Backend on http://0.0.0.0:8000 ...
start "SOP Copilot Backend (Port 8000)" cmd /k "cd /d ""%~dp0"" && call backend\.venv\Scripts\activate.bat && set PYTHONPATH=backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Vite React Frontend on http://0.0.0.0:5173 ...
start "SOP Copilot Frontend (Port 5173)" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo ========================================================
echo   SERVICES STARTED SUCCESSFULLY!
echo.
echo   1. On this Laptop:
echo      Frontend: http://localhost:5173
echo      Backend:  http://localhost:8000/docs
echo.
echo   2. On your Phone / Tablet (Same Wi-Fi):
echo      Frontend: http://192.168.1.3:5173
echo.
echo   * IMPORTANT FOR PHONE:
echo     - Ensure phone is on the SAME Wi-Fi network.
echo     - Type http:// (NOT https://).
echo     - Keep this window and the two server windows OPEN!
echo ========================================================
echo.
pause
