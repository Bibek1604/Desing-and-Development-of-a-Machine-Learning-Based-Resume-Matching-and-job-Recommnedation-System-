@echo off
REM ===========================================================================
REM  SkillMatch backend - one-shot dev setup for Windows Command Prompt (CMD).
REM  Builds a clean Python 3.12 venv, installs minimal deps, sets up SQLite,
REM  and runs migrations. Never uses "activate" - calls the venv python直接.
REM
REM  Usage:  open CMD in this folder and run:   setup-dev.bat
REM  (or just double-click the file)
REM ===========================================================================
setlocal
cd /d "%~dp0"

set "PY312=C:\Users\papisansar\AppData\Local\Python\pythoncore-3.12-64\python.exe"
if not exist "%PY312%" (
    echo [ERROR] Python 3.12 not found at:
    echo         %PY312%
    echo Run  py -3.12 -c "import sys; print(sys.executable)"  and edit the PY312 line.
    pause
    exit /b 1
)

echo.
echo ^>^> Base interpreter:
"%PY312%" --version

echo.
echo ^>^> Recreating .venv ...
if exist .venv rmdir /s /q .venv
"%PY312%" -m venv .venv

echo.
echo ^>^> venv interpreter (must be 3.12.x):
".venv\Scripts\python.exe" --version

echo.
echo ^>^> Installing dependencies (this is the slow step) ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements-min.txt

echo.
echo ^>^> Preparing .env ...
if not exist .env copy .env.example .env >nul
echo    Set DB_PASSWORD in .env before continuing (PostgreSQL is required).

echo.
echo ^>^> Ensuring the PostgreSQL database exists ...
REM  There is no SQLite fallback. If createdb is not on PATH, create the
REM  database manually in pgAdmin:  CREATE DATABASE skillmatch;
where createdb >nul 2>&1
if %ERRORLEVEL%==0 (
    createdb -h localhost -p 5432 -U postgres skillmatch 2>nul
    echo    Database ready ^(or already existed^).
) else (
    echo    createdb not found on PATH - create "skillmatch" in pgAdmin first.
)

echo.
echo ^>^> Applying migrations ...
".venv\Scripts\python.exe" manage.py migrate

echo.
echo ============================================================
echo  Setup complete. Start the server with:
echo      .venv\Scripts\python.exe manage.py runserver
echo  Then open:  http://127.0.0.1:8000/api/docs
echo ============================================================
echo.
pause
endlocal
