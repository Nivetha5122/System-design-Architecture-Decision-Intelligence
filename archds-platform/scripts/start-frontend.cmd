@echo off
setlocal
cd /d "%~dp0..\frontend"
if not exist node_modules (
  echo [ARCHDS] Installing frontend dependencies...
  call npm install
  if errorlevel 1 (
    echo [ARCHDS] npm install failed.
    pause
    exit /b 1
  )
)
echo [ARCHDS] Frontend: http://localhost:5173
npm run dev -- --host 0.0.0.0
endlocal
