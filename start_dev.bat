@echo off
echo ========================================
echo    HospitAI Development Server
echo ========================================
echo.

:: Start Backend API
echo Starting Backend API on port 8000...
start "HospitAI Backend" cmd /k "cd backend && python -m uvicorn api:app --reload --port 8000"

:: Wait a moment for backend to start
timeout /t 3 /nobreak > nul

:: Start Frontend
echo Starting Frontend on port 8080...
start "HospitAI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo    Servers Starting...
echo ========================================
echo.
echo Backend API:  http://localhost:8000
echo API Docs:     http://localhost:8000/docs
echo Frontend:     http://localhost:8080
echo.
echo Close this window to keep servers running.
echo Close the individual terminal windows to stop them.
echo ========================================
pause
