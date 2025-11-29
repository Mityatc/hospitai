@echo off
echo ========================================
echo   HospitAI Development Server Startup
echo ========================================
echo.

echo Starting FastAPI Backend on port 8000...
start "HospitAI API" cmd /k "python -m uvicorn api:app --reload --port 8000"

echo Waiting for API to start...
timeout /t 3 /nobreak > nul

echo Starting React Frontend on port 8080...
cd frontend
start "HospitAI Frontend" cmd /k "npx vite"
cd ..

echo.
echo ========================================
echo   Services Started!
echo ========================================
echo.
echo   API:      http://localhost:8000
echo   Frontend: http://localhost:8080
echo   API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit this window...
pause > nul
