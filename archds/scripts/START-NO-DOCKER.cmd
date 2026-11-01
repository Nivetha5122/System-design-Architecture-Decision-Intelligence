@echo off
setlocal
set "ROOT=%~dp0.."

echo =============================================================
echo   ARCHDS V7.2 - Local PostgreSQL / No Docker
echo =============================================================
echo.

powershell -NoProfile -Command "$c=Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue; if(-not $c.TcpTestSucceeded){exit 1}" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] PostgreSQL is not reachable at localhost:5432.
  echo Start the PostgreSQL Windows service and verify architecture_db exists.
  pause
  exit /b 1
)

where mvn >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Maven was not found in PATH.
  echo Install Maven or open the same terminal where mvn -version works.
  pause
  exit /b 1
)

start "ARCHDS AI :8000" cmd /k "cd /d "%ROOT%ai-service" && if not exist .venv python -m venv .venv && call .venv\Scripts\activate && if not exist .venv\.archds_deps_installed (python -m pip install -r requirements.txt && type nul > .venv\.archds_deps_installed) && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
start "ARCHDS Backend :8080" cmd /k "cd /d "%ROOT%backend" && mvn -Dspring-boot.run.profiles=postgres -Dspring-boot.run.arguments="--spring.datasource.url=jdbc:postgresql://localhost:5432/architecture_db --spring.datasource.username=architecture_user --spring.datasource.password=host" spring-boot:run"
start "ARCHDS Frontend :5173" cmd /k "cd /d "%ROOT%frontend" && if not exist node_modules npm install && npm run dev -- --host 0.0.0.0"

echo.
echo ARCHDS services are starting.
echo Database: PostgreSQL localhost:5432/architecture_db
echo Frontend: http://localhost:5173
echo Backend : http://localhost:8080
echo AI      : http://localhost:8000
echo.
echo IMPORTANT: psql.exe is NOT required by this launcher.
echo Keep all three service windows open.
endlocal
