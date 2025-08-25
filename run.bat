@echo off
setlocal
cd /d %~dp0

REM Detect Python launcher or python
where py >nul 2>nul
if %errorlevel%==0 (
  set PY=py -3
) else (
  set PY=python
)

if not exist .venv (
  echo [+] Creating virtual environment...
  %PY% -m venv .venv
  if %errorlevel% neq 0 (
    echo [!] Failed to create venv. Make sure Python is installed and added to PATH.
    pause
    exit /b 1
  )
  echo [+] Upgrading pip...
  .venv\Scripts\python -m pip install --upgrade pip
  echo [+] Installing requirements...
  .venv\Scripts\pip install -r requirements.txt
)

echo [+] Starting server on http://127.0.0.1:8000
.venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
pause
