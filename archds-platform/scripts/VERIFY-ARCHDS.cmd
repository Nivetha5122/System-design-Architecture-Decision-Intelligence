@echo off
echo Checking ARCHDS services...
echo.
echo [AI SERVICE]
curl -fsS http://localhost:8000/health
if errorlevel 1 echo AI SERVICE NOT READY
echo.
echo [BACKEND]
curl -fsS http://localhost:8080/api/health
if errorlevel 1 echo BACKEND NOT READY
echo.
echo [FRONTEND]
curl -I -s http://localhost:5173/ | findstr /C:"200"
if errorlevel 1 echo FRONTEND NOT READY
echo.
pause
