@echo off
setlocal EnableExtensions
set "ROOT=%~dp0.."
title ARCHDS — Adaptive Architecture Intelligence

echo.
echo  =============================================================
echo    ARCHDS  ^|  Adaptive Architecture Intelligence
echo  =============================================================
echo.

echo [1/3] Starting AI service...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try{Invoke-WebRequest -UseBasicParsing http://localhost:8000/health -TimeoutSec 1 | Out-Null; exit 0}catch{exit 1}"
if errorlevel 1 start "ARCHDS AI Service" cmd /k ""%ROOT%\scripts\start-ai.cmd""

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 30;$i++){try{Invoke-WebRequest -UseBasicParsing http://localhost:8000/health -TimeoutSec 1 | Out-Null; $ok=$true; break}catch{Start-Sleep -Seconds 1}}; if(-not $ok){exit 1}"
if errorlevel 1 (
  echo [ARCHDS] AI service did not become healthy within 30 seconds.
  echo Check the AI terminal for the exact error.
  pause
  exit /b 1
)

echo [2/3] Starting Spring Boot backend...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try{Invoke-WebRequest -UseBasicParsing http://localhost:8080/actuator/health -TimeoutSec 1 | Out-Null; exit 0}catch{exit 1}"
if errorlevel 1 start "ARCHDS Backend" cmd /k ""%ROOT%\scripts\start-backend.cmd""

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 40;$i++){try{Invoke-WebRequest -UseBasicParsing http://localhost:8080/actuator/health -TimeoutSec 1 | Out-Null; $ok=$true; break}catch{Start-Sleep -Seconds 1}}; if(-not $ok){exit 1}"
if errorlevel 1 (
  echo [ARCHDS] Backend did not become healthy within 40 seconds.
  pause
  exit /b 1
)

echo [3/3] Starting React frontend...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try{Invoke-WebRequest -UseBasicParsing http://localhost:5173/ -TimeoutSec 1 | Out-Null; exit 0}catch{exit 1}"
if errorlevel 1 start "ARCHDS Frontend" cmd /k ""%ROOT%\scripts\start-frontend.cmd""

echo.
echo  ARCHDS is starting successfully.
echo  Frontend : http://localhost:5173
echo  Backend  : http://localhost:8080
echo  AI       : http://localhost:8000
echo.
echo  Keep all three service windows open.
echo.
pause
endlocal
