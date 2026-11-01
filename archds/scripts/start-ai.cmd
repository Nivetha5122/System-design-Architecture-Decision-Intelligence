@echo off
setlocal
cd /d "%~dp0..\ai-service"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
if not exist .venv\.archds_deps_installed (
  echo [ARCHDS] Installing AI service dependencies...
  python -m pip install --disable-pip-version-check -r requirements.txt
  if errorlevel 1 (
    echo [ARCHDS] Dependency installation failed.
    pause
    exit /b 1
  )
  type nul > .venv\.archds_deps_installed
)
python -c "from app.main import app; print('[ARCHDS] AI application import: OK')"
if errorlevel 1 (
  echo [ARCHDS] AI application import failed.
  pause
  exit /b 1
)
echo [ARCHDS] AI service listening on http://localhost:8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
endlocal
