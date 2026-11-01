@echo off
setlocal
set ROOT=%~dp0..

echo ==============================================
echo ARCHDS FINAL VERIFICATION
 echo ==============================================

echo.
echo [1/4] AI service unit tests
cd /d "%ROOT%\ai-service"
if not exist .venv (
  echo Creating AI virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pytest -q
if errorlevel 1 goto fail

echo.
echo [2/4] AI health endpoint
curl -fsS http://localhost:8000/health
if errorlevel 1 echo AI service is not running - start scripts\start-ai.cmd first

echo.
echo [3/4] Backend health endpoint
curl -fsS http://localhost:8080/api/health
if errorlevel 1 echo Backend is not running - start scripts\start-backend.cmd first

echo.
echo [4/4] Frontend
curl -I -s http://localhost:5173/ | findstr /C:"200"
if errorlevel 1 echo Frontend is not running - start scripts\start-frontend.cmd first

echo.
echo Verification finished. A failed health check only means that service is not running.
goto end

:fail
echo.
echo AI automated tests FAILED.
exit /b 1

:end
pause
