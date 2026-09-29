@echo off
setlocal EnableExtensions
set "ROOT=%~dp0.."
title ARCHDS — Local Services

echo =============================================================
echo   ARCHDS ^| Local Windows launcher (no Docker)
echo =============================================================

echo [1/3] Checking AI service :8000...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try{Invoke-WebRequest -UseBasicParsing http://localhost:8000/health -TimeoutSec 1 | Out-Null; exit 0}catch{exit 1}"
if errorlevel 1 (
  start "ARCHDS AI :8000" cmd /k "cd /d %ROOT%ai-service && if not exist .venv python -m venv .venv && call .venv\Scripts\activate && if not exist .venv\.archds_deps_installed (python -m pip install -r requirements.txt && type nul > .venv\.archds_deps_installed) && uvicorn app.main:app --host 0.0.0.0 --port 8000"
) else echo [ARCHDS] AI service already healthy; reusing it.

echo [2/3] Checking Spring Boot backend :8080...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try{Invoke-WebRequest -UseBasicParsing http://localhost:8080/actuator/health -TimeoutSec 1 | Out-Null; exit 0}catch{exit 1}"
if errorlevel 1 (
  where mvn >nul 2>nul
  if errorlevel 1 (
    echo [ARCHDS] Maven is not installed or not on PATH.
    echo Install Maven and ensure JAVA_HOME is set, then rerun this script.
    echo Docker Compose remains the recommended zero-setup option.
    pause
    exit /b 1
  )
  start "ARCHDS Backend :8080" cmd /k "cd /d %ROOT%backend && mvn spring-boot:run"
) else echo [ARCHDS] Backend already healthy; reusing it.

echo [3/3] Checking React frontend :5173...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try{Invoke-WebRequest -UseBasicParsing http://localhost:5173/ -TimeoutSec 1 | Out-Null; exit 0}catch{exit 1}"
if errorlevel 1 start "ARCHDS Frontend :5173" cmd /k "cd /d %ROOT%frontend && if not exist node_modules npm install && npm run dev"

echo.
echo Frontend : http://localhost:5173
echo Backend  : http://localhost:8080
echo AI       : http://localhost:8000
echo.
pause
endlocal
