@echo off
cd /d "%~dp0"
echo [1/4] Creating Python virtual environment...
if not exist .venv python -m venv .venv
if errorlevel 1 goto error
echo [2/4] Installing dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
echo [3/4] Creating database and sample data...
.venv\Scripts\python.exe database.py
if errorlevel 1 goto error
echo [4/4] Setup complete! Now double-click run_windows.bat
pause
exit /b 0
:error
echo Setup failed. Please check the error shown above.
pause
exit /b 1
